# cicd.md — Hướng dẫn làm phần Bonus CI/CD (Windows)

> File này bổ sung cho `LAB_GUIDE.md` § *Bonus — CI/CD với GitHub Actions* (dòng
> 648 trở đi). Nó không thay thế phần đó — chỉ nói rõ **trạng thái thật của repo
> bạn** và thứ tự thao tác trên máy Windows, để bạn không mất thời gian đoán mò
> hạ tầng. Nội dung `.github/workflows/ci.yml` bạn phải tự viết — lab cố tình
> không cho sẵn, và `README.md` ghi rõ đây là bài cá nhân (không nhờ ai/AI viết
> hộ), bài chấm dựa trên `tests/test_bonus_cicd.py`.

## 0. Trạng thái đã kiểm tra

- Chưa có thư mục `.github/workflows/` — `test_bonus_cicd.py::workflow_path`
  sẽ `pytest.fail` ngay nếu chạy lúc này.
- Đã deploy CP5 thật lên **Render** (`_guidance/RUN.md` ghi
  `https://day12-chat-an29.onrender.com`), có `render.yaml` sẵn trong repo với
  service `day12-chat` (docker runtime, health check `/healthz`) và
  `day12-chat-redis`.
- `.env.example` có sẵn chỗ cho `DEPLOY_API_TOKEN` — đó là token gọi API của
  chính app bạn (dùng để smoke-test sau khi deploy), **không phải** token
  deploy của Render. Đừng nhầm hai thứ này khi đặt secret ở bước 3.
- README hiện chưa có badge CI nào (`grep badge.svg README.md` không ra gì).
- Remote GitHub: `tuananhpham-vnu/K4-Day12-Cloud-Services-And-Deployment` —
  dùng đúng tên này khi ghép URL badge, đừng chép nhầm tên repo mẫu trong
  `LAB_GUIDE.md`.

## 1. Xác định cơ chế "CD" trước khi viết YAML

Vì bạn dùng **Render** (không phải Railway), cách deploy tự động đơn giản
nhất là **Deploy Hook**:

- Render dashboard → service `day12-chat` → **Settings → Deploy Hook** → copy
  URL (dạng `https://api.render.com/deploy/srv-xxxx?key=yyyy`).
- Gọi `curl` vào URL đó (POST rỗng cũng được) = trigger một lần deploy mới từ
  commit mới nhất trên nhánh đã cấu hình.
- Đây chính là thứ bạn sẽ giấu trong GitHub Secret, **không** phải API token
  của app.

Nếu Render tự động deploy mỗi khi bạn push lên `main` (kiểm tra ở
**Settings → Build & Deploy → Auto-Deploy**), job `deploy` trong workflow vẫn
nên tồn tại — nhưng có thể chỉ cần gọi Deploy Hook để **chủ động** kích hoạt
thay vì phụ thuộc auto-deploy chạy song song không kiểm soát được thứ tự.

## 2. Việc cần làm, theo đúng 8 mục ở `LAB_GUIDE.md` §Bonus

Đọc kỹ dòng 687–792 của `LAB_GUIDE.md` trước khi viết — nó có sẵn khung YAML
cho từng mục (trigger, job `test`, job `build`, job `deploy`, secrets, ghim
version, smoke test, badge). Việc của bạn là **ráp chúng lại đúng thứ tự và
đúng với dự án này**, không phải nghĩ lại từ đầu. Checklist để tự chấm trước
khi push:

- [ ] `on:` có cả `push` (nhánh `main`) và `pull_request` (nhánh `main`)
- [ ] Job test: `actions/checkout` → `actions/setup-python` → `pip install -r
      requirements.txt` → `pytest` **loại trừ** `tests/test_cp5.py` (gọi vào
      service sống) và `tests/test_bonus_cicd.py` (tự tham chiếu badge của
      chính workflow này)
- [ ] Job test có set `env: API_TOKEN: ci-dummy`, `REDIS_URL: "fake://"` —
      không có `.env` trên máy CI, thiếu biến này `Settings` sẽ crash ngay lúc
      import (đúng như Câu 1 trong `exercises.md` bạn vừa đọc — fail fast áp
      dụng ở cả CI)
- [ ] Job build: `docker build -t day12-chat:ci .` chạy được trên runner sạch
- [ ] Job deploy: `needs: [test, build]` **và** `if:` giới hạn
      `github.ref == 'refs/heads/main' && github.event_name == 'push'`
- [ ] Job deploy gọi Deploy Hook: ví dụ
      `curl -fsS -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"`
- [ ] Job deploy có bước smoke test sau deploy: `sleep` rồi
      `curl -fsS https://day12-chat-an29.onrender.com/healthz`
- [ ] Không có chuỗi trông như token dán thẳng vào YAML (`test_khong_hardcode_token`
      quét regex `TOKEN/KEY/SECRET/PASSWORD: "..."` — kể cả để test tạm cũng
      đừng dán thật rồi định xóa sau, nó vẫn nằm trong lịch sử git)
- [ ] Mọi `uses:` ghim version cụ thể, ví dụ `actions/checkout@v4` — không
      `@main`/`@master`/`@latest`

## 3. Đặt Secret trên GitHub (không đụng vào file YAML)

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Tên secret | Giá trị lấy từ đâu |
|---|---|
| `RENDER_DEPLOY_HOOK` | Render → service → Settings → Deploy Hook (bước 1) |

Nếu workflow cần gọi vào `/chat` thật (có auth) trong bước smoke test, thêm
`vars.PUBLIC_URL` (không bí mật, dùng **Variables** chứ không phải Secrets)
trỏ tới `https://day12-chat-an29.onrender.com`.

## 4. Kiểm tra cục bộ trước khi push (đỡ tốn lượt chạy Actions)

```powershell
# 1. YAML hợp lệ không
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml', encoding='utf-8'))"

# 2. Đúng tập test sẽ chạy trong CI (loại cp5 và bonus)
pytest tests/ --ignore=tests/test_cp5.py --ignore=tests/test_bonus_cicd.py -v

# 3. Docker build y hệt bước job build
docker build -t day12-chat:ci .
```

Chỉ sau khi cả ba lệnh trên chạy sạch mới `git push` — mỗi lần push kích hoạt
Actions thật, sửa lỗi cú pháp YAML qua vòng lặp push/xem log rất chậm.

## 5. Thêm badge vào README

Thêm dòng này lên **đầu** `README.md` (trước dòng tiêu đề `# K4 — Ngày 12...`
hoặc ngay sau nó — miễn `test_readme_co_badge` tìm thấy `badge.svg`):

```markdown
![CI](https://github.com/tuananhpham-vnu/K4-Day12-Cloud-Services-And-Deployment/actions/workflows/ci.yml/badge.svg)
```

Lưu ý: tên file `ci.yml` trong URL badge phải khớp **chính xác** tên file bạn
đặt trong `.github/workflows/`.

## 6. Push và xác nhận xanh

```powershell
git add .github/workflows/ci.yml README.md
git commit -m "Them CI/CD voi GitHub Actions"
git push
```

Mở tab **Actions** trên GitHub xem chạy thật. Badge chỉ báo `passing` **sau
khi** ít nhất một lần chạy trên `main` thành công — mở PR trước để kiểm tra CI
mà không đụng `main`, merge xong mới có lần chạy `push` đầu tiên trên `main`
sinh ra badge xanh.

## 7. Chấm điểm

```powershell
pytest tests/test_bonus_cicd.py -v
```

Bài test này gọi thật ra internet để tải badge (`httpx.get`) — nếu vừa push
xong chạy ngay có thể badge chưa kịp cập nhật trạng thái, đợi vài chục giây
rồi chạy lại.
