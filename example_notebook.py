import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy.stats import norm

# ============================================================
# CONFIG
# ============================================================

COLORS = {
    "strategy":  "#2E75B6",
    "benchmark": "#888888",
    "drawdown":  "#D94F4F",
    "positive":  "#2E8B57",
    "negative":  "#D94F4F",
    "grid":      "#E8E8E8",
    "bg":        "#FAFAFA",
}

# ============================================================
# VISUALISATION (backtest_viz.py)
# ============================================================

def plot_results(metrics: dict, save_dir: str = "outputs", benchmark_prices: pd.Series = None):
    Path(save_dir).mkdir(exist_ok=True)

    fig = plt.figure(figsize=(18, 22))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(4, 2, hspace=0.35, wspace=0.3)

    pv          = metrics["portfolio_value"]
    dd          = metrics["drawdown_series"]
    monthly_ret = metrics["monthly_returns"]

    # 1. Equity Curve
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(pv.index, pv.values, color=COLORS["strategy"], linewidth=1.5, label="Strategy")
    ax1.axhline(y=metrics["initial_capital"], color=COLORS["grid"], linestyle="--", alpha=0.5)
    if benchmark_prices is not None:
        bench = benchmark_prices.reindex(pv.index).dropna()
        if len(bench) > 1:
            bench_norm = bench / bench.iloc[0] * metrics["initial_capital"]
            ax1.plot(bench_norm.index, bench_norm.values,
                     color=COLORS["benchmark"], linewidth=1.2, linestyle="--", label="SPY (Buy & Hold)")
    ax1.set_title("Portfolio Value", fontsize=14, fontweight="bold", pad=10)
    ax1.set_ylabel("Value ($)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    ax1.set_facecolor(COLORS["bg"])

    # 2. Drawdown
    ax2 = fig.add_subplot(gs[1, :])
    ax2.fill_between(dd.index, dd.values * 100, 0, color=COLORS["drawdown"], alpha=0.4)
    ax2.plot(dd.index, dd.values * 100, color=COLORS["drawdown"], linewidth=0.8)
    ax2.set_title("Drawdown", fontsize=14, fontweight="bold", pad=10)
    ax2.set_ylabel("Drawdown (%)")
    ax2.grid(True, alpha=0.3)
    ax2.set_facecolor(COLORS["bg"])
    max_dd_date = dd.idxmin()
    ax2.annotate(
        f"Max: {dd.min() * 100:.1f}%",
        xy=(max_dd_date, dd.min() * 100),
        xytext=(30, -20), textcoords="offset points",
        fontsize=9, color=COLORS["drawdown"],
        arrowprops=dict(arrowstyle="->", color=COLORS["drawdown"], lw=1),
    )

    # 3. Monthly returns bar
    ax3 = fig.add_subplot(gs[2, 0])
    colors = [COLORS["positive"] if r >= 0 else COLORS["negative"] for r in monthly_ret.values]
    ax3.bar(monthly_ret.index, monthly_ret.values * 100, width=25, color=colors, alpha=0.7)
    ax3.axhline(y=0, color="black", linewidth=0.5)
    ax3.set_title("Monthly Returns", fontsize=12, fontweight="bold", pad=10)
    ax3.set_ylabel("Return (%)")
    ax3.grid(True, alpha=0.3, axis="y")
    ax3.set_facecolor(COLORS["bg"])
    ax3.xaxis.set_major_locator(mdates.YearLocator())
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # 4. Distribution
    ax4 = fig.add_subplot(gs[2, 1])
    ax4.hist(monthly_ret.values * 100, bins=30, color=COLORS["strategy"], alpha=0.7, edgecolor="white")
    ax4.axvline(x=monthly_ret.mean() * 100, color="red", linestyle="--", linewidth=1,
                label=f"Mean: {monthly_ret.mean() * 100:.2f}%")
    ax4.axvline(x=0, color="black", linewidth=0.5)
    ax4.set_title("Monthly Return Distribution", fontsize=12, fontweight="bold", pad=10)
    ax4.set_xlabel("Return (%)")
    ax4.set_ylabel("Frequency")
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis="y")
    ax4.set_facecolor(COLORS["bg"])

    # 5. Metrics table
    ax5 = fig.add_subplot(gs[3, 0])
    ax5.axis("off")
    metrics_table = [
        ["CAGR",             f"{metrics['cagr']:.2%}"],
        ["Sharpe Ratio",     f"{metrics['sharpe_ratio']:.2f}"],
        ["Sortino Ratio",    f"{metrics['sortino_ratio']:.2f}"],
        ["Max Drawdown",     f"{metrics['max_drawdown']:.2%}"],
        ["Calmar Ratio",     f"{metrics['calmar_ratio']:.2f}"],
        ["Annual Vol.",      f"{metrics['annual_volatility']:.2%}"],
        ["Win Rate",         f"{metrics['win_rate_monthly']:.1f}%"],
        ["Avg Turnover/mo",  f"{metrics['avg_monthly_turnover']:.2%}"],
    ]
    table = ax5.table(
        cellText=metrics_table,
        colLabels=["Metric", "Value"],
        cellLoc="center", loc="center",
        colWidths=[0.5, 0.3],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_facecolor("#2E75B6")
            cell.set_text_props(color="white", fontweight="bold")
        elif i % 2 == 0:
            cell.set_facecolor("#EDF4F8")
        cell.set_edgecolor("#CCCCCC")
    ax5.set_title("Key Metrics", fontsize=12, fontweight="bold", pad=10)

    # 6. Rolling 12M
    ax6 = fig.add_subplot(gs[3, 1])
    if len(monthly_ret) >= 12:
        rolling_12m = (1 + monthly_ret).rolling(12).apply(lambda x: x.prod() - 1, raw=True) * 100
        rolling_12m = rolling_12m.dropna()
        ax6.plot(rolling_12m.index, rolling_12m.values, color=COLORS["strategy"], linewidth=1.2)
        ax6.fill_between(rolling_12m.index, rolling_12m.values, 0,
                         where=rolling_12m.values >= 0, color=COLORS["positive"], alpha=0.2)
        ax6.fill_between(rolling_12m.index, rolling_12m.values, 0,
                         where=rolling_12m.values < 0,  color=COLORS["negative"], alpha=0.2)
        ax6.axhline(y=0, color="black", linewidth=0.5)
    ax6.set_title("Rolling 12M Return", fontsize=12, fontweight="bold", pad=10)
    ax6.set_ylabel("Return (%)")
    ax6.grid(True, alpha=0.3)
    ax6.set_facecolor(COLORS["bg"])

    output_path = f"{save_dir}/backtest_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved: {output_path}")
    return output_path


# ============================================================
# SYNTHETIC BACKTEST
# ============================================================

np.random.seed(42)

dates        = pd.date_range("2015-01-01", "2024-12-31", freq="B")
daily_ret    = np.random.normal(0.0003, 0.012, len(dates))
spy_ret      = np.random.normal(0.00035, 0.010, len(dates))

initial_capital  = 100_000
portfolio_value  = pd.Series(initial_capital * np.cumprod(1 + daily_ret), index=dates)
spy_prices       = pd.Series(150 * np.cumprod(1 + spy_ret), index=dates)

rolling_max      = portfolio_value.cummax()
drawdown_series  = (portfolio_value - rolling_max) / rolling_max

monthly_value    = portfolio_value.resample("ME").last()
monthly_returns  = monthly_value.pct_change().dropna()

n_years     = (dates[-1] - dates[0]).days / 365.25
cagr        = (portfolio_value.iloc[-1] / initial_capital) ** (1 / n_years) - 1
annual_vol  = daily_ret.std() * np.sqrt(252)
sharpe      = (daily_ret.mean() * 252 - 0.045) / annual_vol
downside    = daily_ret[daily_ret < 0].std() * np.sqrt(252)
sortino     = (daily_ret.mean() * 252 - 0.045) / downside
max_dd      = drawdown_series.min()

metrics = {
    "portfolio_value":      portfolio_value,
    "drawdown_series":      drawdown_series,
    "monthly_returns":      monthly_returns,
    "initial_capital":      initial_capital,
    "cagr":                 cagr,
    "sharpe_ratio":         sharpe,
    "sortino_ratio":        sortino,
    "max_drawdown":         max_dd,
    "calmar_ratio":         cagr / abs(max_dd),
    "annual_volatility":    annual_vol,
    "win_rate_monthly":     (monthly_returns > 0).mean() * 100,
    "avg_monthly_turnover": 0.18,
}

# ============================================================
# RUN + DISPLAY
# ============================================================

output_path = plot_results(metrics, save_dir="outputs", benchmark_prices=spy_prices)

from IPython.display import Image
Image(output_path)
