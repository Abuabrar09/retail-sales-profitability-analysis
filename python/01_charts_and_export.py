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

# ---------- Chart 2: operating profit by store ----------
store = df.groupby(["store_id", "store_name", "store_format"], as_index=False)[["net_revenue", "gross_profit"]].sum()
store = store.merge(stores[["store_id", "monthly_operating_cost"]], on="store_id")
store["operating_profit"] = store["gross_profit"] - store["monthly_operating_cost"] * 24
store = store.sort_values("operating_profit")
store["label"] = store["store_name"] + "  (" + store["store_format"] + ")"

fig, ax = plt.subplots(figsize=(10, 7))
colors = [RED if v < 0 else BLUE for v in store["operating_profit"]]
ax.barh(store["label"], store["operating_profit"], color=colors, height=0.7)
ax.axvline(0, color=GREY, linewidth=1)
for y, v in enumerate(store["operating_profit"]):
    ax.text(v + (150 if v >= 0 else -150), y, f"-${abs(v):,.0f}" if v < 0 else f"${v:,.0f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=8, color=GREY)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"))
ax.set_xlim(store["operating_profit"].min() - 2500, store["operating_profit"].max() + 2500)
ax.grid(axis="y", visible=False)
ax.set_title("Operating profit by store, 2024–2025 (after rent, staff & utilities)")
ax.text(0.99, 0.02, "Red = loss-making. All 5 are Express stores.", transform=ax.transAxes,
        ha="right", fontsize=9, color=GREY)
fig.tight_layout()
fig.savefig("images/02_store_operating_profit.png", dpi=150)
print("Saved images/02_store_operating_profit.png")