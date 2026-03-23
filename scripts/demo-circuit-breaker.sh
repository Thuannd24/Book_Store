#!/usr/bin/env bash
# =============================================================================
# demo-circuit-breaker.sh
#
# Script demo Circuit Breaker cho hệ thống BookStore Microservices.
# Chạy trực tiếp trên server để demo trước lớp.
#
# Sử dụng:
#   chmod +x scripts/demo-circuit-breaker.sh
#   ./scripts/demo-circuit-breaker.sh
#
# Yêu cầu: hệ thống đang chạy với docker compose (port 8080 & 8086).
# =============================================================================

# ---------------------------------------------------------------------------
# ANSI color codes
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# Cấu hình endpoint
# ---------------------------------------------------------------------------
GATEWAY="http://localhost:8080"
CART_DIRECT="http://localhost:8086"

CB_STATUS_URL="${GATEWAY}/api/circuit-breakers/"
GATEWAY_HEALTH_URL="${GATEWAY}/api/health/"
CART_VIA_GW_URL="${GATEWAY}/api/gateway/carts/api/carts/customer/1/"
CART_HEALTH_VIA_GW_URL="${GATEWAY}/api/gateway/carts/api/health/"
CART_HEALTH_DIRECT_URL="${CART_DIRECT}/api/health/"

# Circuit Breaker config (phải khớp với api-gateway)
CB_FAILURE_THRESHOLD=3        # số lỗi cần để trigger OPEN (mỗi worker)
CB_RECOVERY_TIMEOUT=30        # giây để chuyển từ OPEN → HALF_OPEN
GUNICORN_WORKERS=3            # số workers của Gunicorn
TOTAL_REQUESTS=12             # requests cần gửi để demo (> workers × threshold)
# Độ trễ giữa các request để Gunicorn kịp phân phối đến worker khác nhau
# (Gunicorn round-robin; 0.3s đủ để mỗi worker nhận ít nhất 1 request)
REQUEST_DELAY=0.3

# Biến global để send_request() trả về HTTP status code mà không ảnh hưởng stdout
LAST_HTTP_CODE=""

# Đường dẫn docker-compose.yml (tự động tìm từ vị trí script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/../docker-compose.yml"

# ---------------------------------------------------------------------------
# Kiểm tra công cụ bắt buộc
# ---------------------------------------------------------------------------
check_dependencies() {
    local missing=0
    for tool in curl docker; do
        if ! command -v "${tool}" >/dev/null 2>&1; then
            echo -e "${RED}Lỗi: công cụ '${tool}' không được tìm thấy. Vui lòng cài đặt trước khi chạy script.${RESET}"
            missing=1
        fi
    done
    # Kiểm tra Docker Compose (V2: 'docker compose', V1: 'docker-compose')
    if command -v docker >/dev/null 2>&1; then
        if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
            echo -e "${RED}Lỗi: không tìm thấy 'docker compose' (V2) hoặc 'docker-compose' (V1). Vui lòng cài đặt Docker Compose.${RESET}"
            missing=1
        fi
    fi
    if [[ "${missing}" -eq 1 ]]; then
        exit 1
    fi
}
check_dependencies

# Wrapper cho docker compose hỗ trợ cả V2 (docker compose) và V1 (docker-compose)
run_compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
    else
        echo -e "${RED}Lỗi: không tìm thấy 'docker compose' hoặc 'docker-compose'.${RESET}" >&2
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Hàm tiện ích
# ---------------------------------------------------------------------------

# In đường kẻ phân cách
separator() {
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${RESET}"
}

# In header của mỗi giai đoạn
phase_header() {
    local phase_num="$1"
    local title="$2"
    echo ""
    separator
    echo -e "${BOLD}${CYAN}  GIAI ĐOẠN ${phase_num}: ${title}${RESET}"
    separator
    echo ""
}

# Dừng lại chờ user nhấn Enter
pause() {
    local msg="${1:-Nhấn [Enter] để tiếp tục...}"
    echo ""
    read -rp "$(echo -e "${YELLOW}▶  ${msg}${RESET}")"
    echo ""
}

# Gửi 1 HTTP request, in status code và response body rút gọn ra terminal.
# HTTP status code được lưu vào biến global LAST_HTTP_CODE để caller đọc lại.
# Hàm KHÔNG dùng echo để trả kết quả qua stdout, tránh bị nuốt khi dùng $(...).
send_request() {
    local label="$1"
    local url="$2"
    local tmp_body
    tmp_body=$(mktemp)

    local http_code
    http_code=$(curl -s -o "${tmp_body}" -w "%{http_code}" --max-time 10 "${url}")
    local body
    body=$(cat "${tmp_body}")
    rm -f "${tmp_body}"

    # Tô màu status code theo loại
    local colored_code
    if [[ "${http_code}" == 2* ]]; then
        colored_code="${GREEN}${http_code}${RESET}"
    elif [[ "${http_code}" == 503 ]]; then
        # 503 = CB OPEN, fast-fail (không gọi downstream)
        colored_code="${YELLOW}${http_code}${RESET}"
    else
        colored_code="${RED}${http_code}${RESET}"
    fi

    printf "  %-40s → HTTP %b\n" "${label}" "${colored_code}"

    # Hiển thị body rút gọn (tối đa 120 ký tự) nếu không phải 2xx
    if [[ "${http_code}" != 2* ]]; then
        local short_body="${body:0:120}"
        echo -e "    ${RED}↳ ${short_body}${RESET}"
    fi

    # Lưu kết quả vào biến global để caller đọc (không dùng echo/return để tránh
    # bị nuốt khi hàm được gọi trong subshell qua $(send_request ...))
    LAST_HTTP_CODE="${http_code}"
}

# Hiển thị CB status dưới dạng bảng có màu
show_cb_status() {
    echo -e "  ${CYAN}Circuit Breaker Status:${RESET}"
    local response
    response=$(curl -s --max-time 5 "${CB_STATUS_URL}")
    if [[ -z "${response}" ]]; then
        echo -e "  ${RED}Không lấy được CB status (gateway chưa sẵn sàng?)${RESET}"
        return
    fi

    # Parse JSON đơn giản bằng grep/sed (không cần jq)
    # Format: {"carts": "CLOSED", "books": "CLOSED", ...}
    echo "${response}" | grep -oE '"[a-zA-Z_-]+": *"[A-Z_]+"' | while IFS= read -r line; do
        local svc state
        svc=$(echo "${line}"  | grep -oE '"[a-zA-Z_-]+"' | head -1 | tr -d '"')
        state=$(echo "${line}" | grep -oE '"[A-Z_]+"' | tail -1 | tr -d '"')

        local colored_state
        case "${state}" in
            CLOSED)    colored_state="${GREEN}${state}${RESET}" ;;
            OPEN)      colored_state="${RED}${state}${RESET}" ;;
            HALF_OPEN) colored_state="${YELLOW}${state}${RESET}" ;;
            *)         colored_state="${state}" ;;
        esac

        printf "    %-20s : %b\n" "${svc}" "${colored_state}"
    done
}

# ---------------------------------------------------------------------------
# Banner giới thiệu
# ---------------------------------------------------------------------------
clear
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║          DEMO CIRCUIT BREAKER – BookStore Microservices      ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Luồng trạng thái Circuit Breaker:"
echo -e "  ${GREEN}CLOSED${RESET} ──(3 lỗi/worker)──▶ ${RED}OPEN${RESET} ──(30s)──▶ ${YELLOW}HALF_OPEN${RESET} ──(1 thành công)──▶ ${GREEN}CLOSED${RESET}"
echo -e "   🟢                            🔴               🟡                          🟢"
echo ""
echo -e "  Hệ thống:"
echo -e "    • API Gateway  : ${GATEWAY}"
echo -e "    • Cart Service : ${CART_DIRECT}"
echo -e "    • CB Config    : failure_threshold=${CB_FAILURE_THRESHOLD}, recovery_timeout=${CB_RECOVERY_TIMEOUT}s"
echo -e "    • Gunicorn     : ${GUNICORN_WORKERS} workers → cần ~$((GUNICORN_WORKERS * CB_FAILURE_THRESHOLD)) requests để tất cả OPEN"
echo ""

pause "Nhấn [Enter] để bắt đầu demo..."

# =============================================================================
# GIAI ĐOẠN 1 – Kiểm tra hệ thống bình thường
# =============================================================================
phase_header "1" "Kiểm tra hệ thống bình thường (tất cả CB CLOSED)"

echo -e "  ${CYAN}→ Kiểm tra CB status (tất cả phải là CLOSED):${RESET}"
show_cb_status
echo ""

echo -e "  ${CYAN}→ Gọi API cart qua gateway (phải thành công):${RESET}"
send_request "GET cart/customer/1 (qua gateway)" "${CART_VIA_GW_URL}"

echo ""
echo -e "  ${CYAN}→ Gọi health check qua gateway:${RESET}"
send_request "GET /api/health/ (gateway)" "${GATEWAY_HEALTH_URL}"

echo ""
echo -e "  ${CYAN}→ Gọi cart health qua gateway:${RESET}"
send_request "GET cart/api/health/ (qua gateway)" "${CART_HEALTH_VIA_GW_URL}"

echo ""
echo -e "  ${CYAN}→ Gọi cart trực tiếp (port 8086):${RESET}"
send_request "GET /api/health/ (trực tiếp)" "${CART_HEALTH_DIRECT_URL}"

echo ""
echo -e "  ${GREEN}✔  Hệ thống hoạt động bình thường. Tất cả CB đang CLOSED.${RESET}"

pause

# =============================================================================
# GIAI ĐOẠN 2 – Tắt cart-service → CB đếm lỗi
# =============================================================================
phase_header "2" "Tắt cart-service → CB đếm lỗi (502 → 503)"

echo -e "  ${YELLOW}→ Đang tắt cart-service...${RESET}"
run_compose -f "${COMPOSE_FILE}" stop cart-service \
    || echo -e "  ${RED}Không thể dừng cart-service tự động. Hãy chạy thủ công: docker compose stop cart-service${RESET}"
echo -e "  ${GREEN}✔  cart-service đã tắt.${RESET}"
echo ""

echo -e "  ${CYAN}→ Gửi ${TOTAL_REQUESTS} requests đến cart qua gateway:${RESET}"
echo -e "  ${YELLOW}   • HTTP 502 = CB CLOSED, gọi downstream thất bại (Upstream unavailable)${RESET}"
echo -e "  ${YELLOW}   • HTTP 503 = CB OPEN, fast-fail ngay (không gọi downstream)${RESET}"
echo ""

count_502=0
count_503=0
count_2xx=0

for i in $(seq 1 "${TOTAL_REQUESTS}"); do
    # send_request in kết quả ra terminal và lưu HTTP code vào LAST_HTTP_CODE
    send_request "Request #${i}" "${CART_VIA_GW_URL}"
    case "${LAST_HTTP_CODE}" in
        502) (( count_502++ )) ;;
        503) (( count_503++ )) ;;
        2*)  (( count_2xx++ )) ;;
    esac
    # Thêm độ trễ nhỏ để Gunicorn kịp phân phối request đến các worker khác
    sleep "${REQUEST_DELAY}"
done

echo ""
echo -e "  ${CYAN}Kết quả:${RESET}"
echo -e "    ${RED}502 (CB CLOSED – downstream fail) : ${count_502}${RESET}"
echo -e "    ${YELLOW}503 (CB OPEN  – fast-fail)        : ${count_503}${RESET}"
echo -e "    ${GREEN}2xx (thành công)                   : ${count_2xx}${RESET}"
echo ""
echo -e "  ${YELLOW}Giải thích:${RESET}"
echo -e "   - Các request đầu tiên nhận 502 vì CB còn CLOSED, gateway cố gọi cart-service nhưng bị từ chối."
echo -e "   - Sau ~${CB_FAILURE_THRESHOLD} lỗi/worker (tổng ~$((GUNICORN_WORKERS * CB_FAILURE_THRESHOLD))), CB chuyển OPEN."
echo -e "   - Các request sau đó nhận 503 ngay lập tức – CB reject mà không gọi downstream."

pause

# =============================================================================
# GIAI ĐOẠN 3 – Kiểm tra CB status → carts phải OPEN
# =============================================================================
phase_header "3" "Kiểm tra CB status → carts phải OPEN"

echo -e "  ${CYAN}→ Kiểm tra CB status:${RESET}"
show_cb_status
echo ""
echo -e "  ${CYAN}→ Kết quả kỳ vọng: 'carts' = ${RED}OPEN${RESET}${CYAN}, các service khác vẫn ${GREEN}CLOSED${RESET}${CYAN}.${RESET}"

pause

# =============================================================================
# GIAI ĐOẠN 4 – Bật lại cart-service + đợi recovery timeout
# =============================================================================
phase_header "4" "Bật lại cart-service + đợi recovery timeout (${CB_RECOVERY_TIMEOUT}s)"

echo -e "  ${YELLOW}→ Đang bật lại cart-service...${RESET}"
run_compose -f "${COMPOSE_FILE}" start cart-service \
    || echo -e "  ${RED}Không thể khởi động cart-service tự động. Hãy chạy thủ công: docker compose start cart-service${RESET}"
echo -e "  ${GREEN}✔  cart-service đã bật lại.${RESET}"
echo ""

echo -e "  ${CYAN}→ Đợi ${CB_RECOVERY_TIMEOUT} giây để CB chuyển OPEN → HALF_OPEN...${RESET}"
for s in $(seq "${CB_RECOVERY_TIMEOUT}" -1 1); do
    printf "\r  ${YELLOW}   Còn lại: %2d giây...${RESET}" "${s}"
    sleep 1
done
printf "\r  ${GREEN}   Đã hết thời gian chờ!                ${RESET}\n"
echo ""

echo -e "  ${CYAN}→ Kiểm tra CB status (carts phải chuyển HALF_OPEN):${RESET}"
show_cb_status
echo ""
echo -e "  ${CYAN}→ Kết quả kỳ vọng: 'carts' = ${YELLOW}HALF_OPEN${RESET}${CYAN}.${RESET}"
echo -e "  ${YELLOW}   Lưu ý: HALF_OPEN chỉ hiển thị khi có request đến sau timeout.${RESET}"
echo -e "  ${YELLOW}   CB sẽ tự chuyển HALF_OPEN ngay khi nhận request tiếp theo.${RESET}"

pause

# =============================================================================
# GIAI ĐOẠN 5 – CB tự phục hồi → CLOSED
# =============================================================================
phase_header "5" "CB tự phục hồi → CLOSED (1 request thành công)"

echo -e "  ${CYAN}→ Gửi 1 request để kích hoạt HALF_OPEN → CLOSED:${RESET}"
send_request "GET cart/customer/1 (trial request)" "${CART_VIA_GW_URL}"
echo ""

echo -e "  ${CYAN}→ Kiểm tra CB status (tất cả phải CLOSED):${RESET}"
show_cb_status
echo ""

echo -e "  ${CYAN}→ Kiểm tra lại health check:${RESET}"
send_request "GET cart/api/health/ (qua gateway)" "${CART_HEALTH_VIA_GW_URL}"
send_request "GET /api/health/ (trực tiếp)"       "${CART_HEALTH_DIRECT_URL}"

pause

# =============================================================================
# Tóm tắt kịch bản demo
# =============================================================================
separator
echo -e "${BOLD}${CYAN}  BẢNG TỔNG KẾT KỊCH BẢN DEMO CIRCUIT BREAKER${RESET}"
separator
echo ""
printf "  %-5s %-35s %-20s %-30s\n" "GĐ" "Hành động" "Trạng thái CB" "Kết quả quan sát"
printf "  %-5s %-35s %-20s %-30s\n" "---" "-----------------------------------" "--------------------" "------------------------------"
printf "  %-5s %-35s %-20s %-30s\n" "1" "Hệ thống bình thường" "🟢 CLOSED" "API hoạt động, dữ liệu trả về"
printf "  %-5s %-35s %-20s %-30s\n" "2" "Tắt cart-service, gửi 12 requests" "🔴 OPEN" "502 → 503 (fast-fail)"
printf "  %-5s %-35s %-20s %-30s\n" "3" "Kiểm tra CB status" "🔴 carts=OPEN" "Các service khác vẫn CLOSED"
printf "  %-5s %-35s %-20s %-30s\n" "4" "Bật lại cart, đợi 30s" "🟡 HALF_OPEN" "CB sẵn sàng thử lại"
printf "  %-5s %-35s %-20s %-30s\n" "5" "Gửi 1 request thử" "🟢 CLOSED" "Hệ thống phục hồi hoàn toàn"
echo ""
separator
echo ""
echo -e "  ${GREEN}${BOLD}✔  Demo hoàn tất! Hệ thống đã phục hồi hoàn toàn.${RESET}"
echo ""
echo -e "  ${CYAN}Điểm chính cần nhớ:${RESET}"
echo -e "   • ${BOLD}502${RESET} – CB vẫn CLOSED, gateway cố gọi downstream nhưng thất bại"
echo -e "   • ${BOLD}503${RESET} – CB đã OPEN, từ chối request ngay (không tốn thời gian chờ)"
echo -e "   • ${BOLD}HALF_OPEN${RESET} – sau ${CB_RECOVERY_TIMEOUT}s, CB cho phép 1 request thử để kiểm tra"
echo -e "   • ${BOLD}CLOSED${RESET} – 1 request thành công → CB phục hồi, hệ thống hoạt động bình thường"
echo ""
separator
echo ""
