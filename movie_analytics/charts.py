from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")

PALETTE = "crest"
ACCENT = "#2a6f97"
WARN = "#c1462c"
GRID = "#d9dde3"


def apply_theme() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.autolayout": True,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.edgecolor": GRID,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "font.size": 9,
        }
    )


def money_formatter(x, _pos=None):
    if abs(x) >= 1e9:
        return f"${x / 1e9:.1f}B"
    return f"${x / 1e6:.0f}M"


def _new_fig(width=7.0, height=4.0):
    apply_theme()
    return plt.subplots(figsize=(width, height))


def missing_values_chart(report: pd.DataFrame):
    data = report[report["% thiếu / % missing"] > 0]
    fig, ax = _new_fig(7, max(2.5, 0.45 * len(data) + 1))
    sns.barplot(data=data, y="Cột / Column", x="% thiếu / % missing", ax=ax, color=WARN)
    ax.set_title("Tỷ lệ dữ liệu thiếu theo cột / Missing rate by column")
    ax.set_xlabel("% thiếu / % missing")
    ax.set_ylabel("")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f%%", padding=3, fontsize=8)
    return fig


def correlation_heatmap(corr: pd.DataFrame):
    fig, ax = _new_fig(6.5, 5)
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Ma trận tương quan / Correlation matrix")
    return fig


def budget_vs_gross_scatter(df: pd.DataFrame, hue: str = "rating_group"):
    fin = df[df["has_financials"]]
    fig, ax = _new_fig(7, 4.8)
    sns.scatterplot(data=fin, x="budget_real", y="gross_real", hue=hue,
                    alpha=0.45, s=18, edgecolor="none", palette="Set2", ax=ax)

    grid = np.linspace(fin["budget_real"].min(), fin["budget_real"].max(), 100)
    ax.plot(grid, grid, "--", color="grey", lw=1, label="Hòa vốn danh nghĩa 1x")
    ax.plot(grid, 2 * grid, "--", color=WARN, lw=1.2, label="Ngưỡng hòa vốn thực tế 2x")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Ngân sách thực 2020 / Budget (real 2020 USD)")
    ax.set_ylabel("Doanh thu thực 2020 / Gross (real 2020 USD)")
    ax.set_title("Ngân sách vs Doanh thu / Budget vs Gross")
    ax.legend(fontsize=7, loc="upper left")
    return fig


def group_bar(table: pd.DataFrame, x: str, y: str, title: str, xlabel: str = "",
              ylabel: str = "", fmt: str = "%.2f", horizontal: bool = True, color=ACCENT):
    fig, ax = _new_fig(7, max(3, 0.42 * len(table) + 1.4))
    if horizontal:
        sns.barplot(data=table, y=x, x=y, ax=ax, color=color)
        ax.set_xlabel(ylabel or y)
        ax.set_ylabel(xlabel or "")
    else:
        sns.barplot(data=table, x=x, y=y, ax=ax, color=color)
        ax.set_xlabel(xlabel or "")
        ax.set_ylabel(ylabel or y)
        ax.tick_params(axis="x", rotation=30)
    ax.set_title(title)
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, padding=3, fontsize=8)
    return fig


def risk_return_scatter(table: pd.DataFrame, label_col: str = "genre"):
    fig, ax = _new_fig(7, 4.8)
    sizes = table["median_budget"] / table["median_budget"].max() * 500 + 40
    ax.scatter(table["loss_rate"], table["median_multiple"], s=sizes,
               c=table["median_multiple"], cmap=PALETTE, alpha=0.85, edgecolor="white")

    for _, row in table.iterrows():
        ax.annotate(row[label_col], (row["loss_rate"], row["median_multiple"]),
                    fontsize=8, xytext=(6, 4), textcoords="offset points")

    ax.axhline(2.0, ls="--", color=WARN, lw=1, label="Ngưỡng hòa vốn 2x")
    ax.axvline(50, ls=":", color="grey", lw=1, label="Tỷ lệ lỗ 50%")
    ax.set_xlabel("Tỷ lệ phim không hòa vốn (%) / Loss rate")
    ax.set_ylabel("Bội số thu hồi vốn trung vị / Median multiple")
    ax.set_title("Bản đồ rủi ro - lợi nhuận (cỡ bóng = ngân sách trung vị)")
    ax.legend(fontsize=7)
    return fig


def trend_lines(trend: pd.DataFrame):
    apply_theme()
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 6), sharex=True)

    axes[0].plot(trend["year"], trend["median_budget"], marker="o", ms=3,
                 color=ACCENT, label="Ngân sách trung vị / Median budget")
    axes[0].plot(trend["year"], trend["median_gross"], marker="o", ms=3,
                 color=WARN, label="Doanh thu trung vị / Median gross")
    axes[0].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(money_formatter))
    axes[0].set_title("Ngân sách & doanh thu trung vị (giá thực 2020)")
    axes[0].legend(fontsize=8)

    axes[1].bar(trend["year"], trend["hit_rate"], color=ACCENT, alpha=0.85)
    axes[1].axhline(50, ls="--", color=WARN, lw=1)
    axes[1].set_title("Tỷ lệ phim đạt ngưỡng hòa vốn 2x (%) / Hit rate")
    axes[1].set_xlabel("Năm / Year")
    fig.tight_layout()
    return fig


def distribution_plot(df: pd.DataFrame, column: str, title: str, log: bool = False):
    series = df[column].dropna()
    if log:
        series = np.log10(series[series > 0])
    fig, ax = _new_fig(7, 3.8)
    sns.histplot(series, bins=40, kde=True, color=ACCENT, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(f"log10({column})" if log else column)
    ax.set_ylabel("Số phim / Titles")
    return fig


def pareto_chart(pareto: pd.DataFrame):
    fig, ax = _new_fig(7, 4)
    idx = np.arange(len(pareto))
    ax.bar(idx - 0.2, pareto["% tổng doanh thu / % of gross"], width=0.4,
           label="% doanh thu / % gross", color=ACCENT)
    ax.bar(idx + 0.2, pareto["% tổng lợi nhuận / % of profit"], width=0.4,
           label="% lợi nhuận / % profit", color=WARN)
    ax.set_xticks(idx)
    ax.set_xticklabels(pareto["Top %"])
    ax.set_xlabel("Nhóm phim dẫn đầu / Top share of titles")
    ax.set_ylabel("% toàn ngành / % of industry")
    ax.set_title("Mức độ tập trung lợi nhuận (Pareto)")
    ax.legend(fontsize=8)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", padding=2, fontsize=7)
    return fig


def boxplot_by_group(df: pd.DataFrame, group: str, value: str, title: str,
                     order=None, clip: float = 10.0):
    fin = df[df["has_financials"]].copy()
    if clip:
        fin = fin[fin[value] <= clip]
    fig, ax = _new_fig(7, max(3.2, 0.4 * fin[group].nunique() + 1.6))
    sns.boxplot(data=fin, y=group, x=value, order=order, ax=ax, palette=PALETTE,
                hue=group, legend=False, showfliers=False)
    ax.axvline(2.0, ls="--", color=WARN, lw=1)
    ax.set_title(title)
    ax.set_ylabel("")
    return fig


def feature_importance_chart(importances: pd.DataFrame):
    fig, ax = _new_fig(7, max(3, 0.4 * len(importances) + 1.2))
    sns.barplot(data=importances, y="feature", x="importance", ax=ax, color=ACCENT)
    ax.set_title("Mức độ quan trọng của biến / Feature importance")
    ax.set_xlabel("Đóng góp / Importance")
    ax.set_ylabel("")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", padding=3, fontsize=8)
    return fig


def prediction_scatter(y_true, y_pred):
    fig, ax = _new_fig(6, 4.6)
    ax.scatter(y_true, y_pred, alpha=0.35, s=16, color=ACCENT, edgecolor="none")
    lims = [min(np.min(y_true), np.min(y_pred)), max(np.max(y_true), np.max(y_pred))]
    ax.plot(lims, lims, "--", color=WARN, lw=1.2)
    ax.set_xlabel("Thực tế / Actual log10(gross)")
    ax.set_ylabel("Dự báo / Predicted log10(gross)")
    ax.set_title("Thực tế vs Dự báo / Actual vs Predicted")
    return fig
