# Kịch bản Demo Circuit Breaker trên PowerShell Windows
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DEMO CIRCUIT BREAKER TRÊN API GATEWAY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$composePath = Join-Path (Get-Location) "docker-compose.yml"

Write-Host "1. Kích hoạt JWT_AUTH_ENABLED trong docker-compose.yml" -ForegroundColor Yellow
# Ghi đè nhanh giá trị trong file yml (Tự động)
(Get-Content $composePath) -replace 'JWT_AUTH_ENABLED: "false"', 'JWT_AUTH_ENABLED: "true"' | Set-Content $composePath
docker compose up -d api-gateway
Start-Sleep -Seconds 5

Write-Host "2. Giả lập sự cố ngắt kết nối Auth-Service!" -ForegroundColor Yellow
docker compose stop auth-service
Start-Sleep -Seconds 2

Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "3. BẮT ĐẦU GỬI 3 REQUESTS THEO TUYẾN TÍNH" -ForegroundColor Cyan
Write-Host "------------------------------------------" -ForegroundColor Cyan
for ($i=1; $i -le 3; $i++) {
    Write-Host "Request #$i (Đang chờ 5s Timeout do Auth Service sập, Gateway bị treo)..." -ForegroundColor Red
    $time = Measure-Command {
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:8080/api/gateway/books/" -Headers @{Authorization="Bearer dummy_token"} -UseBasicParsing
        } catch {
            Write-Host "   => Lỗi trả về: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    Write-Host "   => Chi phí thời gian: $($time.TotalSeconds) giây" -ForegroundColor DarkGray
}

Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "4. GỬI REQUEST THỨ 4 (PHÉP MÀU CIRCUIT BREAKER)" -ForegroundColor Cyan
Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "Lúc này Circuit Breaker phân tích 3 lần Timeout liên tiếp -> Nó MỞ CẦU DAO (OPEN) ngăn sập cả cụm máy chủ Gateway!" -ForegroundColor Green
Write-Host "=> Request sẽ bị Khước từ ngay lập tức (Chưa tới 0.1s Fast-Fail):" -ForegroundColor Green

$timeFastFail = Measure-Command {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:8080/api/gateway/books/" -Headers @{Authorization="Bearer dummy_token"} -UseBasicParsing
    } catch {
        Write-Host "   => Lỗi trả về tức thì: $($_.Exception.Message)" -ForegroundColor Green
    }
}
Write-Host "   => Tổng thời gian ngắt (Circuit Breaker chặn): $($timeFastFail.TotalSeconds) giây" -ForegroundColor Green

Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "5. KHÔI PHỤC LẠI HỆ THỐNG" -ForegroundColor Cyan
Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "Sửa lại file config JWT và khởi động Auth Service bình thường." -ForegroundColor Yellow
(Get-Content $composePath) -replace 'JWT_AUTH_ENABLED: "true"', 'JWT_AUTH_ENABLED: "false"' | Set-Content $composePath
docker compose start auth-service
docker compose up -d api-gateway