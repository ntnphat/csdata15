from __future__ import annotations

import numpy as np
import pandas as pd

from movie_analytics.constants import MIN_TITLES_FOR_RANKING
from movie_analytics.etl import BREAKEVEN_MULTIPLE

FINANCIAL_COLUMNS = ["budget_real", "gross_real", "profit_real", "roi", "multiple"]
NUMERIC_FOR_CORR = ["budget_real", "gross_real", "profit_real", "score", "votes", "runtime", "year"]


def financial_subset(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["has_financials"]].copy()


def kpi_summary(df: pd.DataFrame) -> dict:
    fin = financial_subset(df)
    return {
        "titles": len(df),
        "titles_with_financials": len(fin),
        "coverage_pct": len(fin) / len(df) * 100 if len(df) else np.nan,
        "year_min": int(df["year"].min()) if len(df) else np.nan,
        "year_max": int(df["year"].max()) if len(df) else np.nan,
        "total_budget": fin["budget_real"].sum(),
        "total_gross": fin["gross_real"].sum(),
        "median_budget": fin["budget_real"].median(),
        "median_gross": fin["gross_real"].median(),
        "median_multiple": fin["multiple"].median(),
        "median_roi": fin["roi"].median(),
        "hit_rate": fin["is_profitable_real"].mean() * 100 if len(fin) else np.nan,
        "naive_hit_rate": fin["is_profitable_naive"].mean() * 100 if len(fin) else np.nan,
        "mean_score": df["score"].mean(),
    }


def group_performance(df: pd.DataFrame, by: str, min_count: int = 1) -> pd.DataFrame:
    fin = financial_subset(df)
    if fin.empty:
        return pd.DataFrame()

    grouped = fin.groupby(by, observed=True).agg(
        titles=("name", "count"),
        median_budget=("budget_real", "median"),
        median_gross=("gross_real", "median"),
        total_gross=("gross_real", "sum"),
        median_multiple=("multiple", "median"),
        median_roi=("roi", "median"),
        hit_rate=("is_profitable_real", "mean"),
        mean_score=("score", "mean"),
    )
    grouped["hit_rate"] *= 100
    grouped = grouped[grouped["titles"] >= min_count]
    return grouped.sort_values("median_multiple", ascending=False).reset_index()


def yearly_trend(df: pd.DataFrame) -> pd.DataFrame:
    fin = financial_subset(df)
    trend = fin.groupby("year", observed=True).agg(
        titles=("name", "count"),
        median_budget=("budget_real", "median"),
        median_gross=("gross_real", "median"),
        total_gross=("gross_real", "sum"),
        median_multiple=("multiple", "median"),
        hit_rate=("is_profitable_real", "mean"),
        mean_score=("score", "mean"),
    )
    trend["hit_rate"] *= 100
    return trend.reset_index()


def correlation_matrix(df: pd.DataFrame, columns=None) -> pd.DataFrame:
    columns = columns or NUMERIC_FOR_CORR
    fin = financial_subset(df)
    return fin[columns].corr(numeric_only=True)


def pareto_concentration(df: pd.DataFrame, steps=(0.01, 0.05, 0.10, 0.20, 0.50)) -> pd.DataFrame:
    fin = financial_subset(df).sort_values("profit_real", ascending=False)
    if fin.empty:
        return pd.DataFrame()

    total_profit = fin.loc[fin["profit_real"] > 0, "profit_real"].sum()
    total_gross = fin["gross_real"].sum()
    rows = []
    for step in steps:
        k = max(1, int(round(len(fin) * step)))
        head = fin.head(k)
        rows.append(
            {
                "Top %": f"{step:.0%}",
                "Số phim / Titles": k,
                "% tổng doanh thu / % of gross": head["gross_real"].sum() / total_gross * 100,
                "% tổng lợi nhuận / % of profit": head["profit_real"].sum() / total_profit * 100,
            }
        )
    return pd.DataFrame(rows)


def top_entities(df: pd.DataFrame, by: str, metric: str = "median_multiple",
                 min_titles: int = MIN_TITLES_FOR_RANKING, top_n: int = 15,
                 ascending: bool = False) -> pd.DataFrame:
    table = group_performance(df, by=by, min_count=min_titles)
    if table.empty or metric not in table:
        return table
    return table.sort_values(metric, ascending=ascending).head(top_n).reset_index(drop=True)


def missing_budget_profile(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["nhóm / group"] = np.where(df["budget_real"].isna(), "Thiếu budget / Missing", "Có budget / Present")
    profile = df.groupby("nhóm / group", observed=True).agg(
        titles=("name", "count"),
        median_gross=("gross_real", "median"),
        median_votes=("votes", "median"),
        mean_score=("score", "mean"),
        median_runtime=("runtime", "median"),
        us_share=("country", lambda s: (s == "United States").mean() * 100),
    )
    return profile.reset_index()


def score_vs_money(df: pd.DataFrame, bins=(0, 5, 6, 7, 8, 10)) -> pd.DataFrame:
    fin = financial_subset(df)
    labels = [f"{bins[i]}-{bins[i + 1]}" for i in range(len(bins) - 1)]
    fin = fin.assign(score_band=pd.cut(fin["score"], bins=list(bins), labels=labels, right=False))
    table = fin.groupby("score_band", observed=True).agg(
        titles=("name", "count"),
        median_budget=("budget_real", "median"),
        median_gross=("gross_real", "median"),
        median_multiple=("multiple", "median"),
        hit_rate=("is_profitable_real", "mean"),
    )
    table["hit_rate"] *= 100
    return table.reset_index()


def risk_return_table(df: pd.DataFrame, by: str = "genre", min_count: int = 20) -> pd.DataFrame:
    fin = financial_subset(df)
    table = fin.groupby(by, observed=True).agg(
        titles=("name", "count"),
        median_multiple=("multiple", "median"),
        p25_multiple=("multiple", lambda s: s.quantile(0.25)),
        p75_multiple=("multiple", lambda s: s.quantile(0.75)),
        loss_rate=("is_profitable_real", lambda s: (1 - s.mean()) * 100),
        median_budget=("budget_real", "median"),
    )
    table = table[table["titles"] >= min_count]
    table["spread"] = table["p75_multiple"] - table["p25_multiple"]
    return table.sort_values("median_multiple", ascending=False).reset_index()


BREAKEVEN = BREAKEVEN_MULTIPLE
