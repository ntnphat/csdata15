"""Trợ lý phân tích bằng LangChain + OpenAI.

Cách tiếp cận: không để mô hình tự sinh code chạy trên dữ liệu, mà nạp sẵn các
bảng tổng hợp đã tính bằng Pandas làm NGỮ CẢNH. Con số luôn do Pandas tính,
mô hình chỉ diễn giải - nhờ vậy tránh được nguy cơ bịa số và rủi ro thực thi code.
"""

from __future__ import annotations

import pandas as pd

from movie_analytics import metrics
from movie_analytics.config import get_settings

MAX_ROWS_PER_TABLE = 12

ANSWER_TEMPLATE = """Bạn là chuyên viên phân tích dữ liệu ngành điện ảnh.
Hãy trả lời câu hỏi CHỈ dựa trên NGỮ CẢNH số liệu bên dưới.

Quy tắc:
- Trích dẫn con số cụ thể từ ngữ cảnh, không được tự bịa số.
- Nếu ngữ cảnh không đủ dữ kiện, nói rõ "Dữ liệu hiện có chưa đủ để trả lời".
- Trả lời bằng tiếng Việt, giữ nguyên thuật ngữ chuyên ngành tiếng Anh.
- Trình bày ngắn gọn: kết luận trước, dẫn chứng sau, tối đa 200 từ.
- Mọi giá trị tiền tệ đã quy về USD giá thực năm 2020.

--- NGỮ CẢNH ---
{context}

--- CÂU HỎI ---
{question}

--- TRẢ LỜI ---"""

SUMMARY_TEMPLATE = """Bạn là trưởng nhóm phân tích dữ liệu, đang viết phần tóm tắt
điều hành (executive summary) cho báo cáo về hiệu quả tài chính ngành điện ảnh.

Dựa trên NGỮ CẢNH số liệu, hãy viết:
1. Ba phát hiện quan trọng nhất, mỗi phát hiện kèm số liệu chứng minh.
2. Hai khuyến nghị hành động cụ thể cho nhà đầu tư/hãng phim.
3. Một cảnh báo về giới hạn của dữ liệu.

Viết bằng tiếng Việt, giữ thuật ngữ tiếng Anh, dùng gạch đầu dòng, tối đa 300 từ.

--- NGỮ CẢNH ---
{context}

--- TÓM TẮT ---"""

SUGGESTED_QUESTIONS = [
    "Thể loại nào có hiệu quả đầu tư tốt nhất và vì sao?",
    "Phim gắn nhãn R có phải là khoản đầu tư kém hiệu quả không?",
    "Mùa phát hành ảnh hưởng thế nào tới khả năng hòa vốn?",
    "Ngân sách bao nhiêu là vùng rủi ro cao nhất?",
    "Điểm IMDb cao có đảm bảo phim có lãi không?",
    "Mức độ tập trung lợi nhuận của ngành đang ở đâu?",
]


def is_available() -> bool:
    """Kiểm tra đã có API key và thư viện LangChain hay chưa."""
    if not get_settings().openai_ready:
        return False
    try:
        import langchain_openai  # noqa: F401
        return True
    except ImportError:
        return False


def _table_to_markdown(df: pd.DataFrame, title: str, rows: int = MAX_ROWS_PER_TABLE) -> str:
    """Rút gọn và định dạng một bảng tổng hợp thành markdown cho prompt."""
    if df is None or df.empty:
        return ""
    numeric = df.select_dtypes("number").columns
    trimmed = df.head(rows).copy()
    trimmed[numeric] = trimmed[numeric].round(2)
    return f"### {title}\n{trimmed.to_markdown(index=False)}\n"


def build_context(df: pd.DataFrame) -> str:
    """Đóng gói toàn bộ số liệu cần thiết thành một khối ngữ cảnh duy nhất."""
    kpi = metrics.kpi_summary(df)
    header = (
        "### Tổng quan\n"
        f"- Số phim trong bộ lọc hiện tại: {kpi['titles']:,}\n"
        f"- Số phim có đủ budget & gross: {kpi['titles_with_financials']:,} "
        f"({kpi['coverage_pct']:.1f}%)\n"
        f"- Giai đoạn: {kpi['year_min']} - {kpi['year_max']}\n"
        f"- Ngân sách trung vị: ${kpi['median_budget']:,.0f}\n"
        f"- Doanh thu trung vị: ${kpi['median_gross']:,.0f}\n"
        f"- Bội số thu hồi vốn trung vị (gross/budget): {kpi['median_multiple']:.2f}x\n"
        f"- Tỷ lệ đạt ngưỡng hòa vốn 2.0x: {kpi['hit_rate']:.1f}%\n"
        f"- Điểm IMDb trung bình: {kpi['mean_score']:.2f}\n"
    )

    blocks = [
        header,
        _table_to_markdown(metrics.risk_return_table(df, "genre", 20), "Rủi ro - lợi nhuận theo thể loại"),
        _table_to_markdown(metrics.group_performance(df, "rating_group", 30), "Hiệu quả theo nhãn phân loại"),
        _table_to_markdown(metrics.group_performance(df, "budget_tier", 10), "Hiệu quả theo tầng ngân sách"),
        _table_to_markdown(metrics.group_performance(df, "season", 30), "Hiệu quả theo mùa phát hành"),
        _table_to_markdown(metrics.score_vs_money(df), "Điểm IMDb và hiệu quả tài chính"),
        _table_to_markdown(metrics.pareto_concentration(df), "Mức độ tập trung lợi nhuận"),
        _table_to_markdown(metrics.correlation_matrix(df).round(3).reset_index(names="bien"), "Ma trận tương quan"),
        _table_to_markdown(metrics.top_entities(df, "director", top_n=8)[
            ["director", "titles", "median_budget", "median_multiple", "hit_rate"]], "Top đạo diễn theo bội số"),
        _table_to_markdown(metrics.yearly_trend(df).tail(10), "Xu hướng 10 năm gần nhất"),
    ]
    return "\n".join(block for block in blocks if block)


def _build_chain(template: str):
    """Dựng chain LangChain: prompt -> model -> parser."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    model = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    )
    return PromptTemplate.from_template(template) | model | StrOutputParser()


def ask(df: pd.DataFrame, question: str, context: str = None) -> str:
    """Trả lời câu hỏi của người dùng dựa trên số liệu đã lọc."""
    if not is_available():
        return ("Chưa cấu hình OPENAI_API_KEY hoặc chưa cài langchain-openai. "
                "Vui lòng bổ sung để dùng trợ lý AI.")
    chain = _build_chain(ANSWER_TEMPLATE)
    return chain.invoke({"context": context or build_context(df), "question": question})


def executive_summary(df: pd.DataFrame, context: str = None) -> str:
    """Sinh phần tóm tắt điều hành tự động cho báo cáo."""
    if not is_available():
        return "Chưa cấu hình OPENAI_API_KEY nên không thể sinh tóm tắt tự động."
    chain = _build_chain(SUMMARY_TEMPLATE)
    return chain.invoke({"context": context or build_context(df)})
