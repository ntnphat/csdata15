# 🎬 Movie Investment Analytics

**Đề án cuối khóa — Computer Science Foundation: Data**

Phân tích hiệu quả tài chính của **7.668 bộ phim giai đoạn 1980–2020** và đề xuất chiến
lược phân bổ ngân sách sản xuất. Ứng dụng Streamlit 8 trang, lưu trữ và xác thực bằng
Supabase, trợ lý phân tích bằng LangChain + OpenAI, xuất báo cáo Excel 12 sheet.

---

## Câu hỏi nghiên cứu

> **Yếu tố nào thực sự quyết định hiệu quả tài chính của một bộ phim, và một hãng phim
> nên phân bổ ngân sách như thế nào để giảm xác suất thua lỗ?**

| # | Câu hỏi con | Trang trong app |
|---|---|---|
| Q1 | Dữ liệu có đáng tin không? Thiếu ở đâu và thiếu theo cách nào? | Chất lượng dữ liệu |
| Q2 | Thể loại nào cho hiệu quả vốn tốt nhất trên mỗi đồng đầu tư? | Phân tích chuyên sâu |
| Q3 | Có tồn tại "vùng ngân sách nguy hiểm" không? | Phân tích chuyên sâu |
| Q4 | Nhãn phân loại tuổi và thời điểm phát hành ảnh hưởng ra sao? | Phân tích chuyên sâu |
| Q5 | Có dự báo được doanh thu trước khi phát hành không? | Dự báo doanh thu |

---

## Hai quyết định phương pháp luận then chốt

### 1. Khử lạm phát về USD giá thực 2020

Dữ liệu trải 40 năm nên mọi giá trị tiền tệ được quy đổi bằng chỉ số **CPI-U** (U.S.
Bureau of Labor Statistics):

```
budget_real = budget × (CPI₂₀₂₀ / CPI_năm_phát_hành)
```

CPI 1980 là 82,4 và CPI 2020 là 258,811 → hệ số **3,14 lần**. Không quy đổi thì mọi
so sánh xuyên thời gian đều vô nghĩa.

### 2. Ngưỡng hòa vốn 2,0x thay vì `gross > budget`

Cột `gross` là **doanh thu phòng vé toàn cầu**, không phải tiền hãng phim nhận được:

- Rạp chiếu giữ lại khoảng **50%** tiền vé.
- Chi phí P&A (in ấn & quảng bá) bằng khoảng **50–100% ngân sách sản xuất** và
  **không nằm trong** cột `budget`.

Nên một bộ phim chỉ thực sự hòa vốn khi doanh thu đạt khoảng **2 lần** ngân sách:

| Tiêu chí | Tỷ lệ phim "có lãi" |
|---|---:|
| Ngây thơ: `gross > budget` | 67,8% |
| **Thực tế: `gross ≥ 2 × budget`** | **47,3%** |

Khoảng cách **20,5 điểm phần trăm** này chính là lý do nhiều phân tích phổ biến đánh
giá quá lạc quan về ngành điện ảnh.

---

## Kết quả phân tích

### Bức tranh tổng thể

| Chỉ số | Giá trị |
|---|---:|
| Số phim | 7.668 |
| Số phim đủ dữ liệu tài chính | 5.436 (70,9%) |
| Tổng ngân sách (giá thực 2020) | 267,6 tỷ USD |
| Tổng doanh thu (giá thực 2020) | 747,4 tỷ USD |
| **Bội số thu hồi vốn trung vị** | **1,83x** |
| **Tỷ lệ đạt ngưỡng hòa vốn 2,0x** | **47,3%** |

> **Phát hiện nền tảng:** bộ phim điển hình thu về 1,83 lần ngân sách, trong khi cần
> 2,0 lần mới hòa vốn. **Quá nửa số phim thương mại không thu hồi được vốn.** Đây không
> phải ngành có lợi nhuận ổn định — đây là ngành vận hành theo mô hình đầu tư mạo hiểm.

### 10 phát hiện chính

| # | Phát hiện | Bằng chứng |
|---|---|---|
| 1 | Quá nửa phim thương mại không hòa vốn | Bội số trung vị 1,83x < ngưỡng 2,0x |
| 2 | Lợi nhuận tập trung cực đoan | Top 10% phim = **59,2%** lợi nhuận toàn ngành |
| 3 | **Đường cong chữ U của ngân sách** | Micro 3,38x · **Mid 20–50M chỉ 1,56x** · Blockbuster 2,45x |
| 4 | Horror vượt trội hiệu quả vốn | 3,05x với ngân sách 12,4 triệu; hòa vốn 65,7% |
| 5 | Nghịch lý nhãn R | Điểm IMDb cao nhất (6,50) nhưng bội số thấp nhất (1,55x) |
| 6 | Cửa sổ phát hành là đòn bẩy miễn phí | Hè 2,32x vs Thu 1,38x — chênh **68%** |
| 7 | Tiền không mua được chất lượng | Tương quan `budget ↔ score` = **0,06** |
| 8 | **Không dự báo được doanh thu** | R² = 0,56, sai số trung vị **~2 lần** |
| 9 | **Star power không có bằng chứng** | `star_track` hạng bét; `company_track` quan trọng hơn **13 lần** |
| 10 | Dữ liệu thiếu có hệ thống | Nhóm thiếu budget có doanh thu thấp hơn **8,6 lần** |

### Chi tiết một số phát hiện

**Đường cong chữ U của ngân sách** — hiệu quả không tăng đơn điệu theo vốn:

| Tầng ngân sách | Số phim | Bội số trung vị | Tỷ lệ hòa vốn |
|---|---:|---:|---:|
| Micro (< 5 triệu) | 402 | **3,38x** | **61,9%** |
| Low (5–20 triệu) | 1.313 | 1,77x | 47,1% |
| **Mid (20–50 triệu)** | **1.938** | **1,56x** | **41,5%** ⚠️ |
| High (50–100 triệu) | 1.078 | 1,71x | 44,0% |
| Blockbuster (> 100 triệu) | 705 | **2,45x** | **60,7%** |

Nhóm 20–50 triệu USD vừa **đông nhất** (35,6% danh mục) vừa có tỷ lệ hòa vốn **thấp
nhất** — quá đắt để lỗ nhẹ, quá nhỏ để tạo sự kiện phòng vé. Đây là hiện tượng ngành
gọi là *"cái chết của phim tầm trung"*.

**Hiệu quả vốn theo thể loại** — Horror so với Action:

| | Horror | Action | Chênh lệch |
|---|---:|---:|---|
| Ngân sách trung vị | 12,4 triệu | 56,2 triệu | Action tốn vốn **gấp 4,5 lần** |
| Lợi nhuận trung vị | 29,9 triệu | 41,6 triệu | Action chỉ lãi **gấp 1,4 lần** |
| Tỷ lệ hòa vốn | **65,7%** | 47,3% | Horror an toàn hơn **18 điểm %** |

**Mô hình dự báo trước phát hành** — `score` và `votes` bị loại khỏi biến đầu vào vì
chỉ hình thành **sau** khi phim ra rạp (data leakage). Chia tập theo thời gian, không
chia ngẫu nhiên:

| Mô hình | R² (kiểm định) | Sai số trung vị |
|---|---:|---:|
| **Ridge (tuyến tính)** | **0,559** | **1,95 lần** |
| Random Forest | 0,553 | 2,10 lần |

Kết quả gần như y hệt giữa mô hình tuyến tính và phi tuyến → giới hạn nằm ở **bản chất
bài toán**, không ở thuật toán. **Doanh thu phim về cơ bản không dự báo được từ dữ liệu
tiền phát hành.** Đây là kết luận quan trọng nhất, vì nó dẫn thẳng tới khuyến nghị:
phải quản trị theo **danh mục**, không thể chọn từng phim thắng.

---

## Đề xuất giải pháp

### 1. Chuyển từ quản trị dự án sang quản trị danh mục

Vì top 10% phim tạo 59% lợi nhuận và doanh thu không dự báo được, duyệt từng dự án
theo kỳ vọng lợi nhuận riêng lẻ là cách làm sai về mặt thống kê.

| Tầng | Tỷ trọng vốn đề xuất | Vai trò | Căn cứ |
|---|---:|---|---|
| Micro/Low (< 20 triệu), tập trung Horror | 20–25% | Máy tạo tỷ suất | 3,38x, hòa vốn 61,9% |
| Blockbuster có thương hiệu (> 100 triệu) | 45–55% | Trụ cột dòng tiền | 2,45x, hòa vốn 60,7% |
| **Mid (20–50 triệu)** | **≤ 15%** | **Cắt giảm mạnh** | 1,56x, hòa vốn 41,5% |
| Phim uy tín/giải thưởng | 5–10% | Đầu tư thương hiệu | R & mùa thu đều dưới ngưỡng |

**Nguyên tắc số lượng:** hãng làm 3 phim/năm đang đánh bạc; làm 12–15 phim/năm mới là
đầu tư — danh mục phải đủ lớn để xác suất chứa một cú thắng lớn là đáng kể.

### 2. Thoát khỏi vùng ngân sách chết

Mọi dự án dự kiến 20–50 triệu USD phải chọn một trong hai hướng trước khi phê duyệt:
**kéo xuống dưới 20 triệu** (cắt bối cảnh, bỏ dàn sao đắt tiền — phát hiện 9 cho thấy
điều này gần như không ảnh hưởng doanh thu), hoặc **đẩy lên trên 100 triệu** khi có IP
đủ mạnh. Duy trì ở giữa là lựa chọn tệ nhất.

### 3. Tối ưu cửa sổ phát hành — đòn bẩy chi phí bằng không

Chênh lệch 68% giữa mùa hè và mùa thu mà không tốn thêm đồng nào. Đưa "cửa sổ phát
hành" thành trường **bắt buộc** trong hồ sơ phê duyệt dự án — hiện nó thường là quyết
định muộn của bộ phận phát hành, trong khi dữ liệu cho thấy đây là biến quan trọng
**thứ hai** sau ngân sách.

### 4. Nâng tỷ trọng Horror và Animation theo năng lực

Hãng vốn nhỏ/vừa ưu tiên **Horror** (rải 4–5 dự án bằng chi phí một phim hành động).
Hãng vốn lớn ưu tiên **Animation** (2,93x, độ phân tán thấp nhất, vòng đời khai thác
dài). Cắt giảm **Crime** (1,31x, 62,8% lỗ) trừ khi gắn IP có sẵn.

### 5. Khắc phục vấn đề dữ liệu

| Việc cần làm | Cách làm | Lợi ích |
|---|---|---|
| Bổ sung 28% ngân sách thiếu | The Numbers, Box Office Mojo, TMDB API | Loại bỏ survivorship bias |
| Tách doanh thu nội địa / quốc tế | TMDB, Box Office Mojo | Đánh giá đúng vai trò thị trường quốc tế |
| Bổ sung chi phí P&A | Báo cáo tài chính hãng niêm yết | Thay ước lượng 2,0x bằng lợi nhuận thực |
| Thêm doanh thu streaming | Nielsen, báo cáo hãng | Xử lý đúng các trường hợp như *The Irishman* |
| Chuẩn hóa `genre` đa nhãn | TMDB trả về danh sách thể loại | Hiện mỗi phim chỉ có 1 thể loại chính |
| Tự động hóa cập nhật | Airflow/Prefect + Supabase, chạy hàng tháng | Báo cáo luôn phản ánh dữ liệu mới |

---

## Hạn chế của nghiên cứu

1. **Thiên lệch sống sót.** 28,3% phim thiếu ngân sách **không ngẫu nhiên** — nhóm này
   có doanh thu trung vị thấp hơn 8,6 lần và tỷ lệ phim Mỹ thấp hơn 29 điểm %. Kết luận
   tài chính chỉ đại diện cho **phân khúc phim thương mại có công bố ngân sách**, toàn
   ngành nhiều khả năng kém hơn.
2. **`gross` là doanh thu phòng vé, không phải lợi nhuận hãng phim.** Ngưỡng 2,0x là
   quy tắc ngón tay cái, không phải con số kế toán chính xác cho từng phim.
3. **Không có doanh thu streaming, home video, truyền hình, merchandising.**
   *The Irishman* (phim Netflix, chiếu rạp hạn chế) xuất hiện là "lỗ nặng nhất" — sai
   về bản chất, đúng theo dữ liệu.
4. **Mỗi phim chỉ có một thể loại**, trong khi thực tế phần lớn phim đa thể loại.
5. **Tương quan không phải nhân quả.** Phim mùa hè có bội số cao hơn một phần vì hãng
   phim **chọn** đưa phim mạnh nhất vào mùa hè (selection effect).
6. **Dữ liệu dừng ở 2020 và năm 2020 chỉ có 11 phim** — không kết luận được gì về giai
   đoạn hậu COVID.
7. **CPI-U là chỉ số giá Mỹ**, áp dụng cho cả phim ngoài Mỹ là một xấp xỉ.

---

## Cài đặt và chạy

```bash
python -m venv .venv
.\.venv\Scripts\Activate          # Windows
pip install -r requirements.txt

python -m movie_analytics.etl      # Chạy pipeline làm sạch dữ liệu
python -m streamlit run app.py     # Khởi động ứng dụng
```

Mở `http://localhost:8501` → bấm **Vào bằng chế độ khách**.

App chạy được ngay **không cần cấu hình gì**. Supabase và OpenAI là tùy chọn — thiếu
thì app tự lùi về dữ liệu cục bộ.

> ⚠️ **Nếu gặp lỗi `'streamlit' is not recognized`:** thư mục `Scripts` của Python chưa
> nằm trong PATH. Dùng dạng module `python -m streamlit run app.py` — không phụ thuộc
> PATH và luôn chạy đúng interpreter đang cài thư viện.

### Bật đầy đủ tính năng

Sao chép `.env.example` thành `.env` và điền:

| Biến | Lấy ở đâu | Bật tính năng gì |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` | Supabase → Project Settings → API | Đăng nhập, lưu bộ lọc, lưu lịch sử chat, đồng bộ dữ liệu |
| `OPENAI_API_KEY` | platform.openai.com/api-keys | Trợ lý AI và sinh tóm tắt điều hành |

---

## Thiết lập Supabase

1. Tạo project tại [supabase.com](https://supabase.com) — gói **Free** đủ dùng.
2. Vào **SQL Editor → New query**, dán toàn bộ `sql/schema.sql` và **Run**.
3. Vào **Project Settings → API**, sao chép vào `.env`:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_ANON_KEY`
   - `service_role` → `SUPABASE_SERVICE_KEY` (**không bao giờ commit lên GitHub**)
4. Vào **Authentication → Providers → Email**, bật Email provider. Lúc phát triển nên
   tắt *Confirm email* để đăng ký xong dùng được ngay.
5. Chạy app → trang **⚙️ Quản trị dữ liệu** → tick xác nhận → **Đồng bộ dữ liệu lên
   Supabase**.

### Cấu trúc cơ sở dữ liệu

4 bảng, mỗi bảng bật **Row Level Security**:

| Bảng | Vai trò | Chính sách RLS |
|---|---|---|
| `movies` | Dữ liệu tham chiếu đã làm sạch (5.436+ dòng) | Ai cũng đọc; chỉ `service_role` được ghi |
| `profiles` | Hồ sơ người dùng, khóa ngoại tới `auth.users` | Chỉ đọc/sửa hồ sơ của chính mình |
| `saved_views` | Bộ lọc phân tích người dùng lưu lại (JSONB) | Chỉ thao tác trên dòng của chính mình |
| `chat_logs` | Lịch sử hỏi đáp với trợ lý AI | Chỉ thao tác trên dòng của chính mình |

Trigger `on_auth_user_created` tự tạo hồ sơ khi có tài khoản mới. View
`v_genre_performance` cắm thẳng được vào Power BI.

---

## Triển khai lên Streamlit Community Cloud

1. Push mã nguồn lên GitHub (kiểm tra `.env` **không** bị commit — đã có `.gitignore`).
2. Vào [share.streamlit.io](https://share.streamlit.io) → **New app** → chọn repo.
3. **Main file path:** `app.py`
4. **Advanced settings → Secrets:** dán nội dung theo mẫu `.streamlit/secrets.toml.example`
   với khóa thật.
5. **Deploy.**

`config.py` tự ưu tiên `st.secrets` khi chạy trên Cloud và lùi về `.env` khi chạy máy
cá nhân, nên không cần sửa mã nguồn khi chuyển môi trường.

---

## Các trang trong ứng dụng

| Trang | Nội dung |
|---|---|
| 🔐 **Đăng nhập** | Đăng ký/đăng nhập Supabase Auth, hoặc vào chế độ khách |
| 📊 **Tổng quan** | KPI, scatter ngân sách–doanh thu, Pareto, xu hướng 40 năm, phân bố |
| 🧹 **Chất lượng dữ liệu** | Thống kê thiếu, kiểm định thiên lệch, giải thích ngưỡng 2,0x |
| 🔍 **Phân tích chuyên sâu** | 6 tab: thể loại, ngân sách, phân loại tuổi, mùa, điểm IMDb, tương quan |
| 🏆 **Xếp hạng** | Đạo diễn / diễn viên / hãng phim, có ngưỡng số phim tối thiểu |
| 🤖 **Dự báo doanh thu** | Ridge & Random Forest + mô phỏng kịch bản đầu tư |
| 💬 **Trợ lý AI** | Hỏi đáp trên số liệu đã tổng hợp bằng LangChain + OpenAI |
| 📥 **Xuất báo cáo** | Excel 12 sheet, CSV, lưu bộ lọc lên Supabase |
| ⚙️ **Quản trị dữ liệu** | Chạy lại pipeline ETL, đồng bộ Supabase |

---

## Cấu trúc mã nguồn

```
app.py                    Điểm vào Streamlit: điều hướng + kiểm soát đăng nhập
movie_analytics/          Logic nghiệp vụ (tách hoàn toàn khỏi giao diện)
  ├── constants.py        Bảng CPI-U, ngưỡng, cấu hình nhóm
  ├── config.py           Đọc cấu hình từ st.secrets hoặc .env
  ├── etl.py              Extract - Transform: làm sạch và sinh biến phái sinh
  ├── metrics.py          Toàn bộ hàm tính KPI và bảng tổng hợp
  ├── charts.py           Matplotlib / Seaborn, trả về Figure
  ├── ml.py               scikit-learn: Ridge, Random Forest
  ├── ai.py               LangChain + OpenAI
  ├── db.py               Tầng dữ liệu Supabase + fallback cục bộ
  ├── auth.py             Xác thực qua Supabase Auth
  ├── export.py           Báo cáo Excel bằng Openpyxl
  └── ui.py               Thành phần giao diện dùng chung
views/                    8 trang giao diện
sql/schema.sql            Schema PostgreSQL + Row Level Security
data/movies.csv           Dữ liệu gốc
outputs/                  Bản sạch và báo cáo sinh ra (gitignored)
tests/test_views.py       Kiểm thử cả 8 trang bằng Streamlit AppTest
```

### Nguyên tắc thiết kế

**Tách logic khỏi giao diện.** Mọi tính toán nằm trong `movie_analytics/`, các file
`views/` chỉ gọi hàm và hiển thị. Nhờ vậy con số trong dashboard, trong báo cáo Excel
và trong ngữ cảnh gửi cho AI đều đến từ **cùng một hàm**, không thể lệch nhau.

**Một nguồn sự thật cho mỗi con số.** Đổi ngưỡng hòa vốn từ 2,0x sang 2,5x chỉ cần sửa
hằng số `BREAKEVEN_MULTIPLE` trong `etl.py` — toàn hệ thống cập nhật theo.

**Suy giảm mềm.** App chạy được ở mọi mức cấu hình: không có gì → CSV cục bộ + chế độ
khách; có Supabase → thêm đăng nhập và lưu trữ; có OpenAI → thêm trợ lý AI.

**Trợ lý AI không sinh code.** `ai.build_context(df)` tính sẵn 9 bảng tổng hợp bằng
Pandas từ bộ lọc hiện tại rồi đưa vào prompt — mô hình chỉ diễn giải, không tự chạy
code trên dữ liệu. An toàn hơn và số liệu luôn đúng.

---

## Công nghệ sử dụng

| Công nghệ | Sử dụng ở đâu |
|---|---|
| **Python** | Toàn bộ dự án |
| **Pandas** | `etl.py`, `metrics.py` — làm sạch và toàn bộ tính toán |
| **Matplotlib** | `charts.py` — nền tảng vẽ, định dạng trục tiền tệ, ghép subplot |
| **Seaborn** | `charts.py` — heatmap, boxplot, barplot, histogram + KDE |
| **LangChain** | `ai.py` — chain LCEL `PromptTemplate \| ChatOpenAI \| StrOutputParser` |
| **OpenAI API** | `ai.py` — mô hình `gpt-4o-mini` |
| **Streamlit** | `app.py` + 8 trang trong `views/` |
| **Openpyxl** | `export.py` — báo cáo Excel 12 sheet có định dạng và biểu đồ |
| *Bổ sung:* **Supabase** | `db.py`, `auth.py`, `sql/schema.sql` — lưu trữ và xác thực |
| *Bổ sung:* **scikit-learn** | `ml.py` — Ridge, Random Forest, permutation importance |
| *Bổ sung:* **NumPy** | Tính toán vector hóa |

---

## Kiểm thử

```bash
PYTHONPATH=. python tests/test_views.py
```

Chạy thử cả 8 trang bằng **Streamlit AppTest** để bắt lỗi runtime trước khi deploy.
