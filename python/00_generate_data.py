"""
00_generate_data.py
-------------------
Generates a realistic (synthetic) multi-store retail dataset for the
Retail Sales & Profitability Intelligence project.

Why synthetic? Real store-level P&L data is confidential, so I simulated a
mid-size US grocery/general-merchandise chain with the same quirks you'd find
in a real POS export: seasonality, promotions, returns, duplicate rows,
inconsistent text, and missing values. The cleaning step (01_data_cleaning.py)
handles all of these.

Output (data/raw/):
    stores.csv, products.csv, sales_transactions.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- stores
stores = pd.DataFrame([
    # id, name, city, state, region, format, sq_ft, open_year, monthly_rent
    ("S01", "Dallas Uptown",      "Dallas",       "TX", "South",     "Supercenter", 52000, 2015, 68000),
    ("S02", "Houston Galleria",   "Houston",      "TX", "South",     "Supercenter", 55000, 2014, 72000),
    ("S03", "Austin Domain",      "Austin",       "TX", "South",     "Neighborhood",28000, 2018, 41000),
    ("S04", "San Antonio Pearl",  "San Antonio",  "TX", "South",     "Neighborhood",26000, 2019, 33000),
    ("S05", "Atlanta Midtown",    "Atlanta",      "GA", "South",     "Supercenter", 50000, 2016, 61000),
    ("S06", "Miami Brickell",     "Miami",        "FL", "South",     "Express",     12000, 2021, 39000),
    ("S07", "Phoenix Camelback",  "Phoenix",      "AZ", "West",      "Supercenter", 51000, 2016, 52000),
    ("S08", "Denver LoDo",        "Denver",       "CO", "West",      "Neighborhood",27000, 2017, 38000),
    ("S09", "Los Angeles WeHo",   "Los Angeles",  "CA", "West",      "Express",     11000, 2022, 58000),
    ("S10", "Seattle Capitol Hill","Seattle",     "WA", "West",      "Neighborhood",25000, 2019, 47000),
    ("S11", "Chicago Loop",       "Chicago",      "IL", "Midwest",   "Supercenter", 53000, 2013, 66000),
    ("S12", "Columbus Short North","Columbus",    "OH", "Midwest",   "Neighborhood",26000, 2018, 29000),
    ("S13", "Minneapolis North Loop","Minneapolis","MN","Midwest",   "Neighborhood",24000, 2020, 31000),
    ("S14", "Detroit Midtown",    "Detroit",      "MI", "Midwest",   "Express",     10000, 2022, 21000),
    ("S15", "New York Chelsea",   "New York",     "NY", "Northeast", "Express",     13000, 2020, 82000),
    ("S16", "Boston Back Bay",    "Boston",       "MA", "Northeast", "Neighborhood",25000, 2017, 54000),
    ("S17", "Philadelphia Center","Philadelphia", "PA", "Northeast", "Supercenter", 49000, 2015, 50000),
    ("S18", "Newark Downtown",    "Newark",       "NJ", "Northeast", "Express",     11000, 2023, 36000),
], columns=["store_id", "store_name", "city", "state", "region", "store_format",
            "sq_ft", "open_year", "monthly_rent"]).drop(columns="monthly_rent")

# hidden "true" performance multipliers (traffic & shrink) -> creates under-performers
traffic = {"S01":1.15,"S02":1.20,"S03":1.00,"S04":0.95,"S05":1.05,"S06":0.55,
           "S07":1.00,"S08":0.95,"S09":0.60,"S10":0.90,"S11":1.10,"S12":0.85,
           "S13":0.80,"S14":0.50,"S15":0.75,"S16":0.95,"S17":1.00,"S18":0.45}
shrink_disc = {s: 0.0 for s in stores.store_id}
shrink_disc.update({"S14": 0.06, "S18": 0.07, "S09": 0.04, "S06": 0.03})  # extra markdowns

# ---------------------------------------------------------------- products
cat_def = {
    # category: (subcategories, price range, gross margin range)
    "Fresh Produce": (["Fruits", "Vegetables", "Herbs"],         (0.99, 6.99),  (0.28, 0.42)),
    "Dairy & Eggs":  (["Milk", "Cheese", "Yogurt", "Eggs"],       (1.99, 8.99),  (0.22, 0.34)),
    "Meat & Seafood":(["Beef", "Chicken", "Seafood"],             (5.99, 24.99), (0.18, 0.30)),
    "Bakery":        (["Bread", "Pastries", "Cakes"],             (2.49, 14.99), (0.45, 0.60)),
    "Pantry":        (["Rice & Grains", "Pasta", "Canned Goods", "Spices"], (1.49, 12.99), (0.30, 0.40)),
    "Beverages":     (["Soft Drinks", "Juice", "Coffee & Tea", "Water"],    (0.99, 15.99), (0.32, 0.45)),
    "Snacks":        (["Chips", "Cookies", "Nuts"],               (1.99, 9.99),  (0.38, 0.50)),
    "Frozen":        (["Frozen Meals", "Ice Cream", "Frozen Veg"],(2.99, 11.99), (0.28, 0.38)),
    "Household":     (["Cleaning", "Paper Goods", "Laundry"],     (2.99, 24.99), (0.25, 0.35)),
    "Personal Care": (["Hair Care", "Oral Care", "Skin Care"],    (2.49, 19.99), (0.40, 0.55)),
}
brands = ["Lone Star", "FreshFarm", "Prairie Gold", "Harbor", "Sunvale", "BlueRiver",
          "Golden Fields", "Urban Pantry", "Everyday", "Peak"]

rows, pid = [], 1
for cat, (subs, (pmin, pmax), (mmin, mmax)) in cat_def.items():
    for sub in subs:
        for _ in range(rng.integers(3, 6)):
            price = round(rng.uniform(pmin, pmax), 2)
            margin = rng.uniform(mmin, mmax)
            cost = round(price * (1 - margin), 2)
            brand = rng.choice(brands)
            rows.append((f"P{pid:04d}", f"{brand} {sub} #{pid}", cat, sub, brand, price, cost))
            pid += 1
products = pd.DataFrame(rows, columns=["product_id", "product_name", "category",
                                       "subcategory", "brand", "list_price", "unit_cost"])

# plant real business problems: loss-leaders and badly-negotiated supplier costs
loss_ids = rng.choice(products.product_id, size=9, replace=False)
products.loc[products.product_id.isin(loss_ids), "unit_cost"] = (
    products.loc[products.product_id.isin(loss_ids), "list_price"] * rng.uniform(0.93, 1.08, 9)).round(2)
products["popularity"] = rng.lognormal(0, 0.6, len(products))
# deep-discount promo items (constant heavy promos)
promo_heavy = set(rng.choice(products.product_id, size=8, replace=False))

# ---------------------------------------------------------------- transactions
dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
season = {1:0.88,2:0.86,3:0.95,4:0.97,5:1.00,6:1.02,7:1.05,8:1.00,9:0.96,10:1.00,11:1.12,12:1.25}
dow = {0:0.90,1:0.85,2:0.90,3:0.95,4:1.10,5:1.25,6:1.05}

prod_p = (products.popularity / products.popularity.sum()).values
recs = []
order_no = 100000
for d in dates:
    growth = 1 + 0.06 * ((d - dates[0]).days / 365)          # ~6% YoY growth
    for _, s in stores.iterrows():
        sid = s.store_id
        fmt_base = {"Supercenter": 14, "Neighborhood": 9, "Express": 6}[s.store_format]
        n = rng.poisson(fmt_base * traffic[sid] * season[d.month] * dow[d.dayofweek] * growth)
        if n == 0:
            continue
        picks = rng.choice(len(products), size=n, p=prod_p)
        for i in picks:
            p = products.iloc[i]
            qty = int(rng.choice([1, 1, 1, 2, 2, 3, 4, 6], p=[.3, .15, .1, .15, .1, .1, .05, .05]))
            disc = rng.choice([0, 0, 0, 0, .05, .10, .15, .20, .25])
            if p.product_id in promo_heavy:
                disc = rng.choice([.25, .30, .35, .40])
            if d.month == 11 and d.day >= 24:                       # Black Friday week
                disc = max(disc, .20)
            disc = min(disc + shrink_disc[sid] * rng.random(), 0.60)
            order_no += 1
            recs.append((f"ORD{order_no}", d.strftime("%Y-%m-%d"), sid, p.product_id, qty,
                         p.list_price, round(disc, 2), rng.choice(["Cash", "Credit Card", "Debit Card", "Mobile Pay"],
                                                                   p=[.12, .45, .28, .15]),
                         rng.choice(["Member", "Non-Member"], p=[.55, .45])))

sales = pd.DataFrame(recs, columns=["order_id", "order_date", "store_id", "product_id",
                                    "quantity", "unit_price", "discount_pct",
                                    "payment_method", "customer_type"])

# returns (~2.5%) -> negative quantity rows
ret = sales.sample(frac=0.025, random_state=SEED).copy()
ret["order_id"] = ret["order_id"] + "-R"
ret["quantity"] = -ret["quantity"]
sales = pd.concat([sales, ret], ignore_index=True)

# --------------------------------------------------- inject real-world messiness
dups = sales.sample(n=350, random_state=1)                      # duplicate POS rows
sales = pd.concat([sales, dups], ignore_index=True)
idx = sales.sample(frac=0.004, random_state=2).index            # missing discount
sales.loc[idx, "discount_pct"] = np.nan
idx = sales.sample(frac=0.002, random_state=3).index            # missing payment
sales.loc[idx, "payment_method"] = np.nan
idx = sales.sample(frac=0.01, random_state=4).index             # messy text
sales.loc[idx, "payment_method"] = sales.loc[idx, "payment_method"].str.upper().str.strip() + " "
idx = sales.sample(frac=0.003, random_state=5).index            # alt date format
sales.loc[idx, "order_date"] = pd.to_datetime(sales.loc[idx, "order_date"]).dt.strftime("%m/%d/%Y")
sales = sales.sample(frac=1, random_state=6).reset_index(drop=True)

# monthly operating cost (labour + rent + utilities), scaled to each store's sales volume
opex_ratio = {s: 0.235 for s in stores.store_id}
opex_ratio.update({"S06": 0.30, "S09": 0.31, "S14": 0.33, "S15": 0.29, "S18": 0.36,
                   "S02": 0.21, "S01": 0.215, "S11": 0.22})
_clean = sales[sales.quantity > 0]
_rev = (_clean.quantity * _clean.unit_price * (1 - _clean.discount_pct.fillna(0))).groupby(_clean.store_id).sum() / 24
stores["monthly_operating_cost"] = [round(_rev[s] * opex_ratio[s] * rng.uniform(.97, 1.03), -1) for s in stores.store_id]

products.drop(columns="popularity").to_csv(RAW / "products.csv", index=False)
stores.to_csv(RAW / "stores.csv", index=False)
sales.to_csv(RAW / "sales_transactions.csv", index=False)

print(f"stores: {len(stores)} | products: {len(products)} | sales rows: {len(sales):,}")

