# Movie Investment Analytics

Đề án cuối khóa Computer Science Foundation: Data.

Phân tích hiệu quả tài chính của 7.668 bộ phim phát hành từ 1980 đến 2020, đóng gói
thành một ứng dụng Streamlit 8 trang. Dữ liệu lưu trên Supabase, có đăng nhập, có trợ
lý hỏi đáp bằng LangChain và xuất được báo cáo Excel.

## Câu hỏi

Yếu tố nào quyết định hiệu quả tài chính của một bộ phim, và một hãng phim nên phân bổ
ngân sách thế nào để giảm xác suất thua lỗ?

Đây không phải câu hỏi "phim nào doanh thu cao nhất". Một phim thu 500 triệu từ ngân
sách 300 triệu kém hiệu quả hơn phim thu 100 triệu từ ngân sách 5 triệu, nên tôi đo
bằng tỷ suất chứ không đo bằng quy mô.

## Hai quyết định về cách đo

**Khử lạm phát.** Dữ liệu trải 40 năm. CPI-U năm 1980 là 82,4 còn năm 2020 là 258,811,
tức chênh 3,14 lần. Không quy đổi thì mọi so sánh xuyên thời gian đều sai. Toàn bộ số
tiền trong báo cáo đã đưa về USD giá thực 2020.

**Ngưỡng hòa vốn 2,0x thay vì `gross > budget`.** Cột `gross` là doanh thu phòng vé,
không phải tiền hãng phim nhận được: rạp giữ lại khoảng một nửa tiền vé, còn chi phí
in ấn và quảng bá (P&A) xấp xỉ 50–100% ngân sách sản xuất nhưng không nằm trong cột
`budget`. Vì vậy phim cần thu khoảng 2 lần ngân sách mới thực sự hòa vốn.

Khác biệt giữa hai cách đo rất lớn: theo `gross > budget` thì 67,8% phim "có lãi",
nhưng theo ngưỡng 2,0x chỉ còn 47,3%. Chênh lệch 20 điểm phần trăm này là lý do nhiều
phân tích phổ biến trên mạng đánh giá quá lạc quan về ngành điện ảnh.

## Kết quả

Bội số thu hồi vốn trung vị của toàn bộ dữ liệu là **1,83x**, thấp hơn ngưỡng hòa vốn
2,0x. Nói cách khác, quá nửa số phim thương mại có công bố ngân sách không thu hồi
được vốn. Đây không phải một ngành có lợi nhuận ổn định.

Lợi nhuận tập trung rất đậm: top 10% phim tạo ra 59,2% lợi nhuận toàn ngành, top 20%
tạo ra 78,7%. Nửa dưới đóng góp chưa tới 2%. Cấu trúc này giống ngành đầu tư mạo hiểm
hơn là một ngành sản xuất thông thường.

**Ngân sách không cho hiệu quả tuyến tính mà tạo thành đường cong hình chữ U:**

| Tầng ngân sách | Số phim | Bội số trung vị | Tỷ lệ hòa vốn |
|---|---:|---:|---:|
| Micro (< 5 triệu) | 402 | 3,38x | 61,9% |
| Low (5–20 triệu) | 1.313 | 1,77x | 47,1% |
| Mid (20–50 triệu) | 1.938 | 1,56x | 41,5% |
| High (50–100 triệu) | 1.078 | 1,71x | 44,0% |
| Blockbuster (> 100 triệu) | 705 | 2,45x | 60,7% |

Hai đầu đều tốt, khúc giữa là vùng chết. Nhóm 20–50 triệu vừa đông nhất (35,6% danh
mục) vừa có tỷ lệ hòa vốn thấp nhất — quá đắt để lỗ nhẹ, quá nhỏ để tạo sự kiện phòng
vé. Ngành gọi hiện tượng này là "cái chết của phim tầm trung".

**Kinh dị là thể loại hiệu quả vốn nhất, cách biệt lớn.** Ngân sách trung vị 12,4 triệu
so với 56,2 triệu của phim hành động, tức phim hành động tốn vốn gấp 4,5 lần nhưng lợi
nhuận trung vị chỉ cao hơn 1,4 lần. Tỷ lệ hòa vốn của kinh dị là 65,7% so với 47,3%.
Lý do mang tính cấu trúc: không cần ngôi sao đắt tiền, không cần kỹ xảo tốn kém, có tệp
khán giả trung thành đi xem ngay tuần đầu.

Vài kết quả khác:

- Phim nhãn R được đánh giá cao nhất về nghệ thuật (6,50 điểm IMDb) nhưng có bội số
  thấp nhất (1,55x), vì nhãn R cắt mất khán giả gia đình và tuổi teen.
- Cửa sổ phát hành tạo chênh lệch 68% giữa mùa hè (2,32x) và mùa thu mùa giải (1,38x).
  Đây là biến hoàn toàn nằm trong tầm kiểm soát và không tốn thêm đồng nào.
- Tương quan giữa ngân sách và điểm IMDb chỉ 0,06. Tiền mua được doanh thu nhưng không
  mua được chất lượng.

## Mô hình dự báo

Tôi loại `score` và `votes` khỏi biến đầu vào dù chúng có sức dự báo mạnh nhất, vì
chúng chỉ hình thành sau khi phim ra rạp. Dùng chúng sẽ cho R² đẹp trên giấy nhưng vô
dụng đúng lúc cần ra quyết định. Tập huấn luyện và kiểm định chia theo mốc thời gian
chứ không chia ngẫu nhiên.

Kết quả: Ridge đạt R² 0,559 với sai số trung vị 1,95 lần, Random Forest đạt 0,553 và
2,10 lần. Hai mô hình khác hẳn nhau về bản chất nhưng cho kết quả gần như y hệt, nghĩa
là giới hạn nằm ở bài toán chứ không ở thuật toán.

Sai 2 lần nghĩa là dự báo 100 triệu thì thực tế rơi đâu đó trong khoảng 50–200 triệu.
Với dự án ngân sách 50 triệu, khoảng đó là ranh giới giữa lãi lớn và lỗ nặng. Kết luận
là **không thể chọn đúng phim thắng trước khi phát hành**.

Về độ quan trọng của biến, ngân sách áp đảo mọi thứ còn lại. Đáng chú ý là thành tích
quá khứ của diễn viên chính xếp hạng bét, trong khi thành tích của hãng phim quan trọng
hơn nó 13 lần — năng lực tổ chức sản xuất và phát hành đáng giá hơn tên tuổi trên poster.

## Đề xuất

Vì không dự báo được từng phim, cách quản trị hợp lý là quản theo danh mục thay vì
duyệt từng dự án theo kỳ vọng lợi nhuận riêng lẻ. Cơ cấu tôi đề xuất: 20–25% vốn cho
phim nhỏ tập trung kinh dị, 45–55% cho bom tấn có thương hiệu, cắt nhóm tầm trung xuống
dưới 15%, còn lại dành cho phim uy tín và ghi nhận đó là chi phí thương hiệu chứ không
tính vào chỉ tiêu lợi nhuận.

Với mọi dự án dự kiến 20–50 triệu, nên buộc chọn một trong hai hướng trước khi phê
duyệt: kéo xuống dưới 20 triệu, hoặc đẩy lên trên 100 triệu khi có IP đủ mạnh. Duy trì
ở khoảng giữa là lựa chọn tệ nhất về mặt thống kê.

Cửa sổ phát hành nên là trường bắt buộc trong hồ sơ phê duyệt. Hiện nó thường là quyết
định muộn của bộ phận phát hành, trong khi dữ liệu cho thấy đây là biến quan trọng thứ
hai sau ngân sách.

## Hạn chế

Đây là phần cần đọc trước khi trích dẫn bất kỳ con số nào ở trên.

28,3% phim thiếu ngân sách, và thiếu **không ngẫu nhiên**. Nhóm thiếu có doanh thu
trung vị thấp hơn 8,6 lần, lượt vote thấp hơn 6 lần, tỷ lệ phim Mỹ thấp hơn 29 điểm
phần trăm — nhưng điểm IMDb thì gần như y hệt (6,40 so với 6,39). Đó là phim độc lập
và phim ngoài Hollywood, không có nghĩa vụ công bố tài chính. Nên mọi kết luận tài
chính ở trên chỉ đúng cho phân khúc phim thương mại có công bố ngân sách, còn toàn
ngành nhiều khả năng kém hơn.

Ngoài ra:

- `gross` là doanh thu phòng vé, không phải lợi nhuận hãng phim. Ngưỡng 2,0x là quy tắc
  ngón tay cái của ngành, không phải con số kế toán cho từng phim.
- Không có doanh thu streaming, home video, truyền hình hay merchandising. Vì vậy
  *The Irishman* xuất hiện trong danh sách lỗ nặng nhất — phim Netflix chiếu rạp hạn
  chế để đủ điều kiện tranh Oscar, doanh thu phòng vé gần bằng 0 là do thiết kế.
- Mỗi phim chỉ có một thể loại, trong khi thực tế phần lớn phim đa thể loại.
- Tương quan không phải nhân quả. Phim mùa hè có bội số cao hơn một phần vì hãng phim
  chủ động xếp phim mạnh nhất vào mùa hè.
- Dữ liệu dừng ở 2020 và năm 2020 chỉ có 11 phim, không kết luận được gì về giai đoạn
  hậu COVID.

## Chạy thử

```bash
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

python -m movie_analytics.etl
python -m streamlit run app.py
```

Mở `http://localhost:8501` rồi bấm "Vào bằng chế độ khách". App chạy được ngay mà không
cần cấu hình gì; Supabase và OpenAI đều là tùy chọn.

Nếu shell báo `'streamlit' is not recognized` thì do thư mục `Scripts` của Python chưa
nằm trong PATH. Dùng `python -m streamlit` như trên là xong.

Chạy kiểm thử:

```bash
PYTHONPATH=. python tests/test_views.py
```

Script này mở lần lượt cả 8 trang bằng Streamlit AppTest để bắt lỗi runtime trước khi
deploy.

## Cấu hình

Chép `.env.example` thành `.env` rồi điền. Giá trị nào còn nguyên dạng mẫu (`sk-...`,
`xxxx`) sẽ được coi như chưa khai báo, nên app báo "chưa cấu hình" ngay từ đầu thay vì
lỗi lúc gọi dịch vụ.

| Biến | Lấy ở đâu | Dùng cho |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` | Supabase → Project Settings → API | Đăng nhập, lưu bộ lọc, lưu lịch sử chat, đồng bộ dữ liệu |
| `OPENAI_API_KEY` | platform.openai.com/api-keys | Trợ lý AI, sinh tóm tắt điều hành |

OpenAI API là dịch vụ trả phí, tách khỏi tài khoản ChatGPT. Nếu chưa muốn nạp tiền, trỏ
`OPENAI_BASE_URL` sang một endpoint tương thích chuẩn OpenAI thì `ChatOpenAI` chạy
nguyên si, không sửa dòng code nào:

```bash
# Groq
OPENAI_API_KEY=gsk_...
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
```

Để trống `OPENAI_BASE_URL` thì app dùng OpenAI như mặc định.

## Supabase

1. Tạo project tại supabase.com, gói Free là đủ.
2. Vào SQL Editor, dán toàn bộ `sql/schema.sql` và chạy.
3. Vào Project Settings → API lấy Project URL và hai khóa, điền vào `.env`. Lưu ý lấy
   Project URL chứ không phải REST endpoint (`.../rest/v1/`).
4. Vào Authentication → Providers bật Email. Lúc phát triển nên tắt Confirm email.
5. Chạy app, vào trang Quản trị dữ liệu, tick xác nhận rồi bấm đồng bộ.

Schema gồm 4 bảng, mỗi bảng bật Row Level Security. `movies` là dữ liệu tham chiếu nên
ai cũng đọc được nhưng chỉ `service_role` ghi được. Ba bảng còn lại (`profiles`,
`saved_views`, `chat_logs`) chỉ cho phép mỗi người thao tác trên dòng của chính mình.
Có sẵn trigger tự tạo hồ sơ khi có tài khoản mới và view `v_genre_performance` để cắm
vào Power BI.

Bảng `movies` chỉ lưu dữ kiện. Các cột suy ra được từ dữ kiện đó — cờ nhị phân, biến
logarit — được tính lại khi đọc, để bảng gọn và tránh dữ liệu mâu thuẫn.

## Deploy lên Streamlit Cloud

Push code lên GitHub (kiểm tra `.env` không bị commit), vào share.streamlit.io tạo app
mới, main file là `app.py`, rồi dán khóa vào phần Secrets dạng TOML. Streamlit Cloud
không đọc `.env`.

`config.py` tự ưu tiên `st.secrets` khi chạy trên Cloud và lùi về `.env` khi chạy máy
cá nhân nên không phải sửa code khi chuyển môi trường.

## Cấu trúc

```
app.py                  điểm vào, điều hướng và kiểm soát đăng nhập
movie_analytics/        toàn bộ logic, không phụ thuộc Streamlit
  constants.py          bảng CPI-U, ngưỡng, cấu hình nhóm
  config.py             đọc cấu hình từ st.secrets hoặc .env
  etl.py                làm sạch dữ liệu và sinh biến phái sinh
  metrics.py            các hàm tính KPI và bảng tổng hợp
  charts.py             matplotlib/seaborn
  ml.py                 scikit-learn
  ai.py                 langchain + openai
  db.py, auth.py        supabase
  export.py             báo cáo excel
  ui.py                 thành phần giao diện dùng chung
views/                  8 trang, chỉ gọi hàm và hiển thị
sql/schema.sql          bảng, RLS, trigger, view
data/movies.csv         dữ liệu gốc
outputs/                bản sạch và báo cáo sinh ra, đã gitignore
tests/test_views.py     chạy thử cả 8 trang
```

Mọi tính toán nằm trong `movie_analytics/`, `views/` chỉ hiển thị. Nhờ vậy con số trong
dashboard, trong file Excel và trong ngữ cảnh gửi cho trợ lý AI đều đến từ cùng một hàm
nên không thể lệch nhau. Đổi ngưỡng hòa vốn chỉ cần sửa `BREAKEVEN_MULTIPLE` trong
`etl.py`.

Trợ lý AI không sinh code chạy trên dữ liệu. `ai.build_context()` tính sẵn 9 bảng tổng
hợp bằng Pandas từ bộ lọc hiện tại rồi đưa vào prompt, mô hình chỉ diễn giải. Cách này
an toàn hơn Pandas Agent và số liệu luôn đúng vì do Pandas tính.

## Công nghệ

Python, Pandas, NumPy, Matplotlib, Seaborn, scikit-learn, Streamlit, Supabase
(PostgreSQL + Auth), LangChain, OpenAI API, Openpyxl.
