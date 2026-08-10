# RUN.md — Hướng dẫn chạy lab Day 12 từng bước (Windows)

> File này bổ sung cho `LAB_GUIDE.md`, viết riêng cho môi trường của bạn:
> Windows + PowerShell, Docker Desktop đã cài, và trạng thái thư mục hiện tại
> đã được kiểm tra thực tế. Mỗi bước đều giải thích **vì sao chạy như thế**,
> không chỉ chép lệnh.

## 0. Tình trạng thư mục hiện tại (đã kiểm tra)

Trước khi chạy gì, đây là những gì đang thật sự có trong repo — biết trước để
khỏi ngạc nhiên:

- **Có 2 thư mục virtualenv**: `venv/` và `.venv/`. Chỉ `venv/` có cài đủ
  package (`fastapi`, `uvicorn`, `redis`, `pytest`, `fakeredis`...). `.venv/`
  gần như rỗng (chỉ có `python.exe`). **Dùng `venv/`**, đừng kích hoạt
  `.venv/` — sẽ báo `ModuleNotFoundError` dù bạn đã "cài" trước đó.
  → Việc cần làm: activate đúng `venv\Scripts\Activate.ps1`. Nếu muốn dọn cho
  sạch, xóa `.venv/` đi (không ảnh hưởng gì, cả hai đều bị `.gitignore` bỏ qua
  nên không commit nhầm).
- **`.env` đã tồn tại và đã có `API_TOKEN` được sinh sẵn** — không cần chạy
  lại `cp .env.example .env`. Bạn chỉ cần kiểm tra lại các biến khác (đặc biệt
  `REDIS_URL`) khớp với cách bạn định chạy Redis.
- **Code trong `app/` toàn bộ đang ở dạng khung (`TODO` / `NotImplementedError`)**:
  `Settings` chưa khai báo field nào, `/healthz`, `/readyz`, `/chat` đều
  `raise NotImplementedError`. Đây là trạng thái **CP0** — đúng như lab mô tả
  ("chưa code gì thì test phải rớt gần hết"). Bạn cần tự viết code theo
  `LAB_GUIDE.md` Block 1–4 trước khi các checkpoint pass.
- **`Dockerfile` và `docker-compose.yml`** cũng đang ở bản nháp một-stage /
  thiếu service `chat` — cần sửa ở Block 2.
- Docker Desktop đã cài (`docker version 29.4.3`) — dùng được ngay cho CP2 trở đi.

Vì sao nói rõ điều này trước: RUN.md không thể "chạy hộ" phần code — lab được
thiết kế để bạn tự viết `app/*.py`. File này chỉ đảm bảo **hạ tầng chạy đúng**
(venv, Redis, Docker, pytest) để mỗi lần bạn sửa code, bạn kiểm tra được ngay
kết quả, thay vì bị chặn bởi lỗi môi trường.

---

## 1. Kích hoạt đúng virtualenv

```powershell
venv\Scripts\Activate.ps1
```

Vì sao: mọi lệnh `python`, `pip`, `pytest`, `uvicorn` sau đó phải trỏ vào
Python đã cài sẵn `fastapi`/`redis`/`pytest`. Nếu bạn quên activate (hoặc lỡ
activate `.venv`), `import fastapi` sẽ báo `ModuleNotFoundError` — không phải
vì code sai mà vì đang chạy nhầm interpreter.

Xác nhận đã đúng môi trường:

```powershell
python -c "import fastapi, uvicorn, redis, pytest; print('OK')"
```

Nếu PowerShell chặn script (`... cannot be loaded because running scripts is
disabled`), mở PowerShell với quyền phù hợp và chạy một lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 2. Kiểm tra `.env`

`.env` đã có sẵn — mở lên đối chiếu với bảng dưới, không cần tạo lại:

| Biến | Giá trị hiện tại | Có cần đổi không |
|------|------------------|-------------------|
| `API_TOKEN` | đã có token ngẫu nhiên | Không — giữ nguyên, đây là secret của riêng bạn |
| `REDIS_URL` | `redis://localhost:6379/0` | Giữ nguyên **nếu** bạn sẽ chạy Redis bằng Docker (bước 3). Đổi thành `fake://` chỉ khi thật sự chưa dùng được Docker |
| `PORT` | 8000 | Giữ nguyên khi chạy local |

Vì sao `.env` không được commit: nó nằm trong `.gitignore` (`.env` được liệt
kê rõ ở đầu file). Bạn có thể tự kiểm tra bất cứ lúc nào bằng:

```powershell
git ls-files | Select-String "^\.env$"
```

Không có output nào → an toàn, `.env` chưa từng được `git add`.

---

## 3. Bật Redis bằng Docker

```powershell
docker compose up -d redis
docker compose ps
```

Vì sao chạy Redis riêng trước khi động vào code: Block 1 (`config.py`,
`logging_utils.py`, `/healthz`) chưa cần Redis, nhưng Block 3–4 thì có. Bật
sẵn từ đầu để không bị chặn giữa chừng, và cột `STATE` trong `docker compose
ps` phải là `running (healthy)` — healthcheck của service `redis` (đã cấu
hình sẵn trong `docker-compose.yml`) tự kiểm tra bằng `redis-cli ping`.

Chưa cài Docker Desktop hoặc daemon chưa bật? Đặt tạm:

```
REDIS_URL=fake://
```

trong `.env`. `fake://` trỏ vào một Redis giả chạy trong RAM (dùng
`fakeredis`, đã có trong `requirements.txt`) — đủ cho CP0/CP1/CP3/CP4 nhưng
**không thay thế được cho CP2 (build Docker image) và CP5 (deploy)**, hai
checkpoint đó bắt buộc Docker thật.

---

## 4. Checkpoint 0 — xác nhận pytest chạy được

```powershell
pytest tests/ -v -m "not docker"
```

Vì sao kỳ vọng là **rớt gần hết**: đúng như hiện trạng đã kiểm tra ở mục 0 —
`app/` toàn `TODO`. Mục đích của CP0 không phải "code đúng" mà là xác nhận
ba thứ:
1. `pytest` chạy được (không có lỗi cú pháp import ngăn cả bộ test khởi động)
2. Bạn đọc được thông báo lỗi pytest in ra (đây sẽ là công cụ chính bạn dùng
   suốt buổi)
3. Không có `ModuleNotFoundError`/`ImportError` — nếu có, quay lại bước 1.

`-m "not docker"` bỏ qua các test cần build image (chậm, và Block 2 chưa tới).

---

## 5. Block 1 — viết `config.py`, `logging_utils.py`, `/healthz`

Chạy thử app sau khi sửa từng phần:

```powershell
uvicorn app.main:app --reload --port 8000
```

Ở cửa sổ PowerShell khác:

```powershell
curl.exe -i http://localhost:8000/healthz
```

Vì sao dùng `curl.exe` chứ không phải `curl`: PowerShell có alias `curl` trỏ
vào `Invoke-WebRequest`, cú pháp khác hẳn (không hỗ trợ `-i`, `-X`, `-H` kiểu
Unix). Gõ `curl.exe` để chắc chắn gọi đúng binary curl thật, đúng cú pháp
`LAB_GUIDE.md` dùng.

Chấm điểm riêng phần này:

```powershell
pytest tests/test_cp1.py -v
```

Vì sao chạy riêng từng file test thay vì cả `tests/`: khi đang sửa Block 1,
các lỗi ở Block 3/4 (chưa code tới) sẽ làm nhiễu output, khó thấy lỗi thật sự
liên quan đến phần đang làm.

---

## 6. Block 2 — Docker

### 6.1 Sửa `Dockerfile` theo 6 yêu cầu ghi trong chính file, rồi build:

```powershell
docker build -t day12-chat:prod .
docker images day12-chat:prod
```

Vì sao build ngay sau mỗi lần sửa: lỗi Dockerfile (sai thứ tự `COPY`, quên
`--from=builder`, `.dockerignore` loại nhầm file cần) chỉ lộ ra lúc build,
không lộ ra lúc đọc code. Build sớm, build thường xuyên, thay vì sửa xong cả
6 yêu cầu rồi mới build một lần và phải dò lỗi trong mớ thay đổi lớn.

### 6.2 Sửa `docker-compose.yml`, thêm service `chat`, rồi:

```powershell
docker compose up -d
docker compose ps
curl.exe http://localhost:8000/healthz
docker compose logs chat
```

Vì sao `docker compose logs chat` là lệnh đầu tiên cần chạy khi container tắt
ngay sau khi start: nguyên nhân phổ biến nhất là `Settings` (Block 1) ném
`ValidationError` vì thiếu biến môi trường trong container — log sẽ in traceback
đầy đủ, khác hẳn với debug qua `curl` (chỉ báo "connection refused", không nói
tại sao).

### 6.3 Checkpoint

```powershell
pytest tests/test_cp2.py -v
pytest tests/test_cp2.py -v -m "not docker"   # phần cấu trúc, nhanh hơn
```

---

## 7. Block 3 — API Security (`auth.py`, `rate_limiter.py`, `cost_guard.py`, `/chat`)

Sau khi viết xong, chạy app (local hoặc qua compose) rồi test thủ công theo
đúng thứ tự 401 → 200 → 429 ghi trong `LAB_GUIDE.md` §Block 3. Trên
PowerShell, nạp token vào biến trước để khỏi gõ lại:

```powershell
$env:API_TOKEN = (Get-Content .env | Select-String "^API_TOKEN=").ToString().Split("=")[1]

curl.exe -i -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $env:API_TOKEN" -H "X-Client-Id: sv01" `
  -d '{\"message\":\"Docker la gi?\"}'
```

Vì sao đọc token từ `.env` bằng lệnh thay vì copy-paste tay: token là secret
sinh ngẫu nhiên, copy tay dễ dính khoảng trắng/thiếu ký tự cuối, gây lỗi 401
"khó hiểu" (token đúng mà vẫn bị từ chối) — nguồn lỗi phổ biến nhất khi test
thủ công.

Checkpoint:

```powershell
pytest tests/test_cp3.py -v
```

---

## 8. Block 4 — Scaling & Reliability (`store.py`, `/readyz`, `lifecycle.py`)

```powershell
docker compose up -d --scale chat=3
docker compose ps
```

Vì sao scale ra 3 container ngay khi test tính "stateless": bug kinh điển của
Block 4 là lưu lịch sử hội thoại trong biến Python toàn cục (`dict` trong
RAM). Với 1 container, bug này **không lộ ra** — mọi request đều rơi vào cùng
một process. Chỉ khi có ≥2 container, request thứ 2 của cùng một client có
thể rơi vào container khác, và nếu state nằm trong RAM thay vì Redis, lịch sử
"biến mất". Đây là lý do lab bắt buộc test bằng `--scale chat=3` chứ không
phải chạy 1 container là đủ.

Checkpoint:

```powershell
pytest tests/test_cp4.py -v
```

---

## 9. Block 5 — Deploy lên cloud

Theo đúng `LAB_GUIDE.md` §Block 5 (Railway hoặc Render). Sau khi có URL công
khai, điền `DEPLOYMENT.md` — **chỉ điền tên biến, không dán giá trị
`API_TOKEN`** (đã có cảnh báo rõ trong file đó và trong README, vì repo sẽ
public).

Checkpoint:

```powershell
pytest tests/test_cp5.py -v
```

Không deploy được (không có thẻ, mạng chặn...)? Dùng phương án dự phòng:
đặt `LOCAL_FALLBACK=true` trong `.env`, `docker compose up -d`, chụp màn hình
vào `screenshots/`. Vì sao vẫn phải chụp và chạy được `docker compose ps`:
CP5 dạng dự phòng vẫn cần chứng minh service *chạy thật* ở đâu đó — chỉ khác
là "công khai trên Internet" hay "chạy trên máy bạn", không phải bỏ qua hẳn
việc chứng minh service hoạt động.

---

## 10. Wrap-up

```powershell
# 1. Trả lời 10 câu trong exercises.md

# 2. Chấm thử
python grade.py

# 3. Kiểm tra .env không bị commit
git ls-files | Select-String "^\.env$"
# Có output → DỪNG LẠI, .env đang bị track, gỡ ra trước khi commit tiếp

# 4. Nộp
git add -A
git commit -m "Hoan thanh lab Day 12"
git push
```

Vì sao chạy `python grade.py` **trước** khi commit lần cuối, không phải sau:
điểm số phản ánh đúng những gì `pytest` thấy tại thời điểm đó — chạy trước
cho bạn cơ hội sửa nốt phần còn đỏ, chạy sau chỉ để biết điểm mà không kịp sửa.

---

## Tổng hợp lệnh dùng nhiều nhất (tra nhanh)

```powershell
venv\Scripts\Activate.ps1                    # luôn chạy đầu tiên mỗi phiên PowerShell mới
pytest tests/test_cpN.py -v                  # kiểm tra một checkpoint
pytest tests/ -v -m "not docker"             # toàn bộ, bỏ qua test build (nhanh)
pytest tests/test_cpN.py -x --tb=short       # dừng ở lỗi đầu tiên, traceback gọn
docker compose up -d redis                   # chỉ Redis (đủ cho Block 1)
docker compose up -d                         # cả redis + chat (từ Block 2 trở đi)
docker compose logs chat                     # container tắt ngay sau start → xem đây trước
docker compose down -v                       # dọn sạch, kể cả volume Redis
python grade.py                              # điểm tổng, chạy trước khi nộp
```
