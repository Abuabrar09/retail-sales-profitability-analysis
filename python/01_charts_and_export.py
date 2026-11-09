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

# ---------- Chart 3: gross margin by category ----------
cat = df.groupby("category")[["net_revenue", "gross_profit"]].sum()
cat["margin_pct"] = cat["gross_profit"] / cat["net_revenue"] * 100
cat = cat.sort_values("margin_pct")
company_margin = df["gross_profit"].sum() / df["net_revenue"].sum() * 100

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(cat.index, cat["margin_pct"], color=BLUE, height=0.7)
ax.axvline(company_margin, color=GREY, linewidth=1, linestyle="--", zorder=0.5)
ax.text(company_margin + 0.5, len(cat) - 0.4, f"Company average {company_margin:.1f}%", fontsize=9, color=GREY)
for y, (m, rev) in enumerate(zip(cat["margin_pct"], cat["net_revenue"])):
    ax.text(m + 0.5, y, f"{m:.1f}%   (revenue ${rev/1000:,.0f}K)", va="center", fontsize=8, color=GREY,
            bbox=dict(facecolor="#fcfcfb", edgecolor="none", pad=1), zorder=5)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.set_xlim(0, cat["margin_pct"].max() + 15)
ax.grid(axis="y", visible=False)
ax.set_title("Gross margin by category: high revenue does not mean high profit")
fig.tight_layout()
fig.savefig("images/03_category_margin.png", dpi=150)
print("Saved images/03_category_margin.png")

# ---------- Chart 4: loss-making products ----------
prod = df.groupby(["product_name", "category"], as_index=False).agg(
    gross_sales=("gross_sales", "sum"), discounts=("discount_amount", "sum"),
    gross_profit=("gross_profit", "sum"), unit_price=("unit_price", "max"), unit_cost=("unit_cost", "max"))
losers = prod[prod["gross_profit"] < 0].copy()
cost_high = losers["unit_cost"] / losers["unit_price"] >= 0.9
disc_high = losers["discounts"] / losers["gross_sales"] >= 0.25
losers["cause"] = "Over-discounted"
losers.loc[cost_high, "cause"] = "Supplier cost too high"
losers.loc[cost_high & disc_high, "cause"] = "Both"
losers = losers.sort_values("gross_profit", ascending=False)

fig, ax = plt.subplots(figsize=(10, 6.5))
ax.barh(losers["product_name"], losers["gross_profit"], color=RED, height=0.7)
for y, (v, c) in enumerate(zip(losers["gross_profit"], losers["cause"])):
    ax.text(v - 150, y, f"-${abs(v):,.0f}  · {c}", va="center", ha="right", fontsize=8, color=GREY)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"))
ax.set_xlim(losers["gross_profit"].min() * 1.75, 0)
ax.yaxis.tick_right()
ax.spines["right"].set_visible(True)
ax.spines["left"].set_visible(False)
ax.grid(axis="y", visible=False)
ax.set_title(f"{len(losers)} products sold at a loss: -${abs(losers['gross_profit'].sum()):,.0f} gross profit")
fig.tight_layout()
fig.savefig("images/04_loss_making_products.png", dpi=150)
print("Saved images/04_loss_making_products.png")

# ---------- Chart 5: do discounts pay off? ----------
bins = [-0.001, 0, 0.15, 0.25, 1]
labels = ["No discount", "1–15%", "16–25%", "Over 25%"]
df["discount_band"] = pd.cut(df["discount_pct"], bins=bins, labels=labels)
band = df.groupby("discount_band", observed=True).agg(
    revenue=("net_revenue", "sum"), profit=("gross_profit", "sum"), avg_units=("quantity", "mean"))
band["margin_pct"] = band["profit"] / band["revenue"] * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# left panel: margin collapses
colors = [RED if m < 0 else BLUE for m in band["margin_pct"]]
ax1.bar(band.index, band["margin_pct"], color=colors, width=0.6)
ax1.axhline(0, color=GREY, linewidth=1)
for x, m in enumerate(band["margin_pct"]):
    ax1.text(x, m + (1 if m >= 0 else -1), f"{m:.1f}%", ha="center",
             va="bottom" if m >= 0 else "top", fontsize=9, color=GREY)
ax1.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax1.set_ylim(band["margin_pct"].min() - 6, band["margin_pct"].max() + 6)
ax1.grid(axis="x", visible=False)
ax1.set_title("Gross margin by discount band")

# right panel: customers do not buy more
ax2.bar(band.index, band["avg_units"], color=BLUE, width=0.6)
for x, u in enumerate(band["avg_units"]):
    ax2.text(x, u + 0.03, f"{u:.2f}", ha="center", va="bottom", fontsize=9, color=GREY)
ax2.set_ylim(0, band["avg_units"].max() * 1.3)
ax2.grid(axis="x", visible=False)
ax2.set_title("Average units per sale by discount band")

fig.suptitle("Bigger discounts do not sell more units; they only cut margin",
             x=0.01, ha="left", fontsize=14, fontweight="bold")
fig.tight_layout()
fig.savefig("images/05_discount_effectiveness.png", dpi=150)
print("Saved images/05_discount_effectiveness.png")