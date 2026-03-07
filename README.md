# BookStore Microservices (Django REST)

Academic 12-service BookStore system built with Django REST Framework. Each service is independent with its own database; communication is REST over HTTP only and proxied externally through `api-gateway`.

---

## Yêu cầu

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (đã bật và đang chạy)
- [Node.js >= 18](https://nodejs.org/) (cho Frontend)
- Git

---

## Chạy Backend

### Bước 1 — Clone và vào thư mục dự án

```bash
git clone <repo-url>
cd bookstore-microservices
```

### Bước 2 — Build và khởi động tất cả services

```bash
docker-compose up -d --build
```

> Lần đầu sẽ mất vài phút để pull image và cài dependencies.  
> Mỗi service sẽ tự động chạy `makemigrations` + `migrate` khi khởi động.

### Bước 3 — Kiểm tra các container đang chạy

```bash
docker ps
```

Tất cả 12 service + 12 database phải có trạng thái `Up`.

### Bước 4 — Tạo tài khoản lần đầu (PowerShell)

**Staff** (nhân viên):
```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8081/api/staff/register/" `
  -Method POST -ContentType "application/json" `
  -Body '{"staff_code":"S001","full_name":"Alice Admin","email":"staff@example.com","password":"secret123","role":"admin","department":"IT"}' `
  | Select-Object -ExpandProperty Content
```

**Manager** (quản lý):
```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8082/api/managers/register/" `
  -Method POST -ContentType "application/json" `
  -Body '{"manager_code":"M001","full_name":"Bob Manager","email":"manager@example.com","password":"secret123"}' `
  | Select-Object -ExpandProperty Content
```

**Customer** (khách hàng — có thể đăng ký qua web):
```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8083/api/customers/register/" `
  -Method POST -ContentType "application/json" `
  -Body '{"full_name":"Nguyen Van A","email":"customer@example.com","password":"secret123","phone":"0901234567","address":"123 Le Loi, HCM"}' `
  | Select-Object -ExpandProperty Content
```

---

## Chạy Frontend

### Bước 1 — Cài dependencies

```bash
cd frontend-web
npm install
```

### Bước 2 — Khởi động dev server

```bash
npm run dev
```

Frontend chạy tại: **http://localhost:3000**

> Vite proxy tự động chuyển tiếp `/api/*` → `http://localhost:8080` (api-gateway).  
> Không cần cấu hình thêm.

---

## Đăng nhập

| Vị trí | URL | Email | Password |
|---|---|---|---|
| Customer | http://localhost:3000/login | `customer@example.com` | `secret123` |
| Staff | http://localhost:3000/staff/login | `staff@example.com` | `secret123` |
| Manager | http://localhost:3000/manager/login | `manager@example.com` | `secret123` |

---

## Dừng Backend

```bash
docker-compose down
```

Để xóa toàn bộ dữ liệu database:
```bash
docker-compose down -v
```

---

## Services & Ports

| Service | Host Port | Trách nhiệm |
| --- | --- | --- |
| api-gateway | 8080 | Proxy tập trung |
| staff-service | 8081 | Tài khoản nhân viên |
| manager-service | 8082 | Quản lý & dashboard |
| customer-service | 8083 | Khách hàng & profile |
| catalog-service | 8084 | Danh mục sách |
| book-service | 8085 | Sách & tồn kho |
| cart-service | 8086 | Giỏ hàng |
| order-service | 8087 | Đơn hàng |
| ship-service | 8088 | Vận chuyển |
| pay-service | 8089 | Thanh toán |
| comment-rate-service | 8090 | Đánh giá & bình luận |
| recommender-ai-service | 8091 | Gợi ý sách |



## Repository Layout
```
api-gateway/                # proxy
book-service/               # books CRUD + internal validator
cart-service/               # carts and items
catalog-service/            # categories
comment-rate-service/       # reviews & averages
customer-service/           # customers + auto-cart creation
manager-service/            # managers + dashboard summary
order-service/              # orders + payment & shipment orchestration
pay-service/                # payments
recommender-ai-service/     # rule-based recommendations
ship-service/               # shipments
staff-service/              # staff accounts
docs/architecture|api|demo|report
postman/                    # collections (placeholders)
docker-compose.yml
.gitignore
README.md
```

## Documentation
- Per-service README files describe endpoints, env vars, setup, and curl examples.
- Additional notes live under `docs/`.

## Cleanup
`.gitignore` excludes venv, __pycache__, pyc, db.sqlite3, and other artifacts to keep the repo clean.
