"""
01_charts_and_export.py
Turns the SQL findings into charts for the README and exports
a clean dataset for Excel and the dashboard.
"""
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ---------- 1. Load the clean data from the database ----------
con = duckdb.connect("retail.duckdb", read_only=True)
df = con.sql("SELECT * FROM sales_enriched").df()
stores = con.sql("SELECT * FROM stores").df()
print(f"Loaded {len(df):,} clean transactions")

# ---------- 2. Export clean data for Excel / dashboard ----------
df.to_csv("data/processed/sales_clean.csv", index=False)
print("Saved data/processed/sales_clean.csv")

# ---------- 3. Chart style (same look for every chart) ----------
BLUE, ORANGE, RED, GREY = "#2a78d6", "#eb6834", "#d03b3b", "#52514e"
plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": GREY,
    "xtick.color": GREY, "ytick.color": GREY,
    "axes.grid": True, "grid.color": "#ebeae6", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "font.size": 10, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
})
dollars = mtick.StrMethodFormatter("${x:,.0f}")

# ---------- Chart 1: monthly revenue and gross profit ----------
df["month"] = pd.to_datetime(df["order_date"]).dt.to_period("M").dt.to_timestamp()
monthly = df.groupby("month")[["net_revenue", "gross_profit"]].sum()

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(monthly.index, monthly["net_revenue"], color=BLUE, linewidth=2, marker="o", markersize=4, label="Net revenue")
ax.plot(monthly.index, monthly["gross_profit"], color=ORANGE, linewidth=2, marker="o", markersize=4, label="Gross profit")
for m in monthly.index[monthly.index.month == 11]:          # shade Black Friday months
    ax.axvspan(m - pd.Timedelta(days=14), m + pd.Timedelta(days=14), color=GREY, alpha=0.08)
nov = pd.Timestamp("2025-11-01")
ax.annotate("November (Black Friday):\nmargin dips to ~22.5%", (nov, monthly.loc[nov, "gross_profit"]),
            xytext=(-170, -45), textcoords="offset points", fontsize=9, color=GREY,
            arrowprops=dict(arrowstyle="-", color=GREY, lw=0.8))
ax.yaxis.set_major_formatter(dollars)
ax.set_ylim(0)
ax.set_title("Monthly net revenue and gross profit, 2024–2025")
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig("images/01_monthly_trend.png", dpi=150)
print("Saved images/01_monthly_trend.png")