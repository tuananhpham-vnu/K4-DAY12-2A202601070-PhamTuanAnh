# Phiếu Phản Ánh — K4 Ngày 12
### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Mình từng quên set biến `API_TOKEN` trên dashboard Render trước khi bấm
> deploy. Vì `api_token` không có mặc định, `Settings()` raise lỗi ngay lúc
> khởi động, container không lên được và Render báo fail tức thì. Mình biết
> ngay có gì đó sai, sửa xong deploy lại là hết chuyện.
>
> Nếu để mặc định `"changeme"`, app vẫn chạy bình thường, `/healthz` vẫn
> trả 200, nhìn vào tưởng mọi thứ ổn. Nhưng lúc đó ai gửi
> `Authorization: Bearer changeme` cũng xác thực được, coi như `/chat` public
> hoàn toàn. Sự cố chỉ lộ ra khi hóa đơn LLM tăng bất thường — tức là phát
> hiện sau khi đã mất tiền, không phải trước khi mất.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log thật lấy từ `emit()` khi gọi `/chat`:
>
> ```json
> {"event": "chat_completed", "severity": "INFO", "ts": "2026-08-10T10:27:24.489842+00:00", "client_id": "sv-demo", "prompt_tokens": 2, "completion_tokens": 34, "usd_cost": 2.07e-05}
> ```
>
> Vì log là JSON có key rõ ràng, mình lọc và truy vấn được theo từng trường —
> ví dụ chạy `jq` để chỉ lấy những dòng có `usd_cost` vượt ngưỡng, hoặc lọc
> theo `client_id` trên dashboard Cloud Logging. `print` chỉ là một chuỗi
> text, muốn lọc phải đoán regex và dễ vỡ mỗi khi câu chữ đổi.
>
> Ngoài ra các số như `usd_cost`, `prompt_tokens` nằm trong field riêng nên
> tính toán được trực tiếp — cộng dồn chi phí theo ngày, vẽ biểu đồ token
> dùng theo thời gian, hoặc tự động cảnh báo khi vượt ngưỡng. `print` không
> tách số ra khỏi câu chữ, nên máy không tính được gì từ đó.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1690 MB |
| Multi-stage | 270 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Đo thật trên máy mình bằng `docker images chat --format "{{.Size}}"`:
> `chat:single` = 1.69GB, `chat:multi` = 270MB, chênh khoảng 1.4GB.
>
> Phần lớn chênh lệch đến từ base image. `python:3.11` (bản một stage) mang
> theo cả toolchain build như gcc, make, header hệ thống — nặng gần 1GB chỉ
> riêng phần base, còn `python:3.11-slim` đã bỏ hết những thứ đó. Phần còn
> lại đến từ việc image một stage giữ luôn compiler và cache pip trong layer
> cuối, vì `pip install` chạy ngay tại đó. Bản multi-stage cài dependency ở
> stage `builder` riêng, rồi chỉ copy đúng phần đã cài xong
> (`COPY --from=builder /install /usr/local`) sang stage runtime, không mang
> theo compiler hay rác build.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Mình thêm một dòng vào cuối `app/main.py` rồi build lại. Stage `builder`
> (`COPY requirements.txt`, `RUN pip install`) vẫn CACHED vì nội dung
> `requirements.txt` không đổi. `RUN useradd` cũng CACHED vì không phụ thuộc
> source code. Chỉ có `COPY app ./app` và `COPY utils ./utils` phải chạy
> lại, vì Docker cache từng layer theo hash nội dung input, mà nội dung thư
> mục `app/` đã đổi.
>
> Nếu đặt `COPY . .` lên trước `RUN pip install`, mỗi lần sửa một dòng code
> sẽ làm layer `COPY . .` mất cache, kéo theo mọi layer sau nó — kể cả
> `pip install` — cũng phải chạy lại, dù `requirements.txt` không hề đổi.
> Kết quả là build chậm hẳn, vì lần nào cũng cài lại toàn bộ dependency thay
> vì chỉ copy code mới.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Một lỗ hổng trong dependency hoặc trong cách xử lý input cho phép kẻ tấn
> công chạy được lệnh shell bên trong container. Nếu process đang chạy bằng
> root, lệnh đó lập tức có quyền root trong container — đọc ghi mọi file,
> cài thêm phần mềm độc hại. Từ đó, nếu container còn bị cấu hình lỏng lẻo
> thêm, ví dụ mount `/var/run/docker.sock` hay chạy `--privileged`, quyền
> root trong container có thể leo thang thành quyền root trên chính host.
>
> Lệnh `USER appuser` chặn đứng chuỗi này ngay ở bước quyền hạn: kẻ tấn công
> vẫn có thể chạy được lệnh, nhưng lệnh đó chỉ mang quyền user thường
> (`uid 10001`). Không ghi được vào thư mục hệ thống, không cài được
> service, và nếu có escape ra ngoài thì cũng chỉ mang theo quyền user
> thường trên host — thiệt hại giảm hẳn so với chạy root mặc định.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

> `WWW-Authenticate` là header bắt buộc theo chuẩn HTTP cho mọi response
> 401, vì nó cho client biết phải xác thực bằng phương thức nào. Thiếu
> header này, một client tuân thủ chuẩn chỉ biết bị từ chối chứ không biết
> phải gửi lại request theo scheme gì.
>
> Trả cùng một thông báo lỗi cho cả ba trường hợp là để không hé lộ thông
> tin cho kẻ đang dò token. Nếu phân biệt rõ "thiếu header" với "token sai",
> kẻ tấn công có thể dùng sự khác biệt đó để thu hẹp dần phạm vi đoán — biết
> chắc phần header đã đúng, chỉ còn phải mò giá trị token. Trả lỗi giống hệt
> nhau, cùng với so sánh bằng `compare_digest` để không rò rỉ qua thời gian
> phản hồi, khiến kẻ tấn công không có tín hiệu nào để biết mình đang gần
> đúng hay sai hoàn toàn.

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

> `refill_per_second` bằng `10/60 ≈ 0.1667`. Sau 10 phút, tức 600 giây im
> lặng, lượng token muốn nạp thêm là `600 × 0.1667 = 100`.
>
> Với `min(capacity, ...)` như code hiện tại, xô dù im lặng bao lâu cũng
> không vượt quá 10, nên client gửi được đúng 10 request liên tiếp trước khi
> request thứ 11 bị 429.
>
> Nếu bỏ `min(capacity, ...)`, token cộng dồn không giới hạn, xô sẽ có
> `10 + 100 = 110` token sau 10 phút, và client gửi liên tiếp được 110
> request mới bị chặn — gấp 11 lần sức chứa danh nghĩa. Refill vốn là hàm
> tuyến tính theo thời gian trôi qua, nên thiếu bước `min()` thì im lặng
> càng lâu, token tích càng nhiều, và một client rảnh cả ngày có thể bùng nổ
> hàng chục nghìn request trong vài giây — đúng điều token bucket được dựng
> ra để ngăn.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

> Với hạn mức $30/tháng, `CostGuard` chỉ chặn khi tổng chi tiêu trong cả
> tháng vượt 30 đô, nên một client gọi liên tục từ 2h sáng có thể đốt gần
> hết 30 đô trước khi bị chặn, tùy phần ngân sách còn lại của tháng đó. Tệ
> hơn, nếu sự cố xảy ra đầu tháng khi ngân sách còn nguyên, thiệt hại có thể
> lên tới gần 30 đô chỉ trong một đêm, và service không tự hồi phục cho tới
> đầu tháng sau.
>
> Với hạn mức $1/ngày như code hiện tại, khóa Redis `spend:{client}:{ngày}`
> đổi theo từng ngày, nên thiệt hại tối đa của một sự cố bị giới hạn ở đúng
> 1 đô — dù sự cố kéo dài bao lâu trong ngày đó. Sang ngày mới, key đổi
> sang một ngày khác, `spent()` tự trả về 0 vì key cũ không tồn tại, và
> client lại có ngân sách mới mà không cần ai can thiệp. Hạn mức ngày vừa
> giới hạn thiệt hại tối đa xuống 1/30, vừa tự hồi phục sau tối đa 24 giờ.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Redis mất kết nối. Cả `/healthz` gộp chung lẫn `/readyz` đều gọi
> `store.ping()` nên cùng trả 503 trên cả 3 container cùng lúc, vì cả ba đều
> phụ thuộc chung một Redis. Orchestrator đọc `/healthz` như liveness probe,
> thấy 503 liên tục qua vài lần kiểm tra, kết luận process "chết" và bắt đầu
> restart cả 3 container gần như đồng thời.
>
> Trong lúc đó Redis vẫn chưa hồi phục, nên container vừa restart xong gọi
> lại `/healthz` vẫn nhận 503, lại bị đánh giá là chết, lại restart tiếp —
> cả cụm rơi vào vòng lặp crash-restart trong suốt 30 giây Redis mất kết
> nối, thay vì chỉ đơn giản ngừng nhận traffic mới như readiness lẽ ra phải
> làm. Khi Redis nối lại được, cụm không hồi phục ngay lập tức mà còn mất
> thêm thời gian khởi động lại từ vòng crash-loop cuối cùng, downtime kéo
> dài hơn hẳn so với việc tách riêng hai endpoint như thiết kế ban đầu.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> *Câu trả lời của bạn*
