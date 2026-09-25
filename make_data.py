#!/usr/bin/env python3
"""Transform raw AYS pulls into the report payload (data.json, plaintext).
Month-grained so the dashboard can filter by any date range client-side, and
carries real gross profit (floor cost from the catalog).

Inputs: raw_granular.json (cust/item/custgp x month, with floor cost),
        raw_items.json (item buyer lists), raw_icust.json (item-window customers),
        config.json
Output: data.json  (encrypted into index.html by build_site.py)
"""
import json, os, re, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
def load(p):
    with open(os.path.join(HERE, p)) as f:
        return json.load(f)
cfg = load("config.json")
icust = load("raw_icust.json")

def parse_wrapped(path):
    raw = open(os.path.join(HERE, path)).read()
    d = json.loads(raw[raw.find("{"):])
    cols = [c["name"] for c in d["result_set"]["resultSetMetaData"]["rowType"]]
    return [dict(zip(cols, r)) for r in d["result_set"]["data"]]

gran = parse_wrapped("raw_granular.json")
items_raw = parse_wrapped("raw_items.json")   # ITEM, BUYERS, SPEND, CASES, AVG_CASE_PRICE, BUYER_LIST

def f(x):
    return float(x) if x not in (None, "") else 0.0
def i(x):
    return int(float(x)) if x not in (None, "") else 0

# ---------- category rules (AYS has no taxonomy; derived from item names) ----------
RULES = [
    ("Gloves", ["glove", "vitrile", "nitrile"]),
    ("Cups & Lids", ["portion cup", "portion lid", "shot cup", "foam cup", "cup", "lid"]),
    ("To-Go & Containers", ["to go box", "to go container", "togo", "hinged", "clamshell",
        "deli container", "foam container", "paper container", "container", "food tray",
        " tray", "bowl", "plate", "pizza box", "carrier", "steam pan", "foil pan"]),
    ("Napkins", ["napkin"]),
    ("Wraps, Foil & Film", ["foil", "film", "deli wrap", "wax paper", "butcher paper",
        "steak paper", "pan liner", "wrap"]),
    ("Bags & Can Liners", ["can liner", "liner", "portion bag", "sos bag", "grocery bag",
        "thank you bag", "bag", "trash"]),
    ("Paper & Register", ["paper towel", "towel", "tissue", "register roll", "thermal",
        "bond", "ink ribbon", "guest check", "label", "roll towel"]),
    ("Cutlery & Picks", ["cutlery", "fork", "knife", "teaspoon", "spoon", "skewer",
        "toothpick", "pick", "stir straw", "napkin band"]),
    ("Straws", ["straw"]),
    ("Cleaning & Chemicals", ["cleaner", "bleach", "detergent", "sanitiz", "soap", "scrub",
        "scour", "degreaser", "grill brick", "sponge", "mop", "eraser", "clorox", "pine-sol",
        "windex", "comet", "griddle screen", "steramine", "n2o"]),
    ("Beverage & Syrups", ["syrup", "smoothie", "monin", "torani", "grenadine", "juice",
        "creamer", "tea filter", "milk"]),
    ("Food", ["food", "sauce", "ketchup", "mayonnaise", "mayo", "cheese", "beef", "shrimp",
        "crab", "tuna", "sausage", "butter", "margarine", "bun", "bread", "hoagie", "pie",
        "parfait", "salt", "pepper", "seasoning", "vinegar", "pickle", "okra", "green bean",
        "asparagus", "potato", "tortilla", "pasta", "linguini", "crackers", "olive", "garlic",
        "honey", "sriracha", "teriyaki", "soy", "panko", "breader", "dressing", "coleslaw",
        "custard", "avocado", "cherries", "pollock", "cod", "clam", "andouille", "kielbasa",
        "bacon", "oil", "soup", "lime", "lemon", "mustard", "hot sauce", "seafood", "roll"]),
]
def categorize(name):
    n = (name or "").lower()
    for cat, kws in RULES:
        for kw in kws:
            if kw in n:
                return cat
    return "Other / Uncategorized"

# ---------- month-grained series ----------
cust_month, item_month, custgp_month = [], [], []
cust_rep = {}
for r in gran:
    k = r["KIND"]; m = r["MONTH"]
    if k == "cust":
        cust_month.append({"c": r["NAME"], "rep": r["REP"], "m": m,
                           "s": round(f(r["SALES"]), 2), "cs": round(f(r["CASES"]), 1), "o": i(r["ORDERS"])})
        cust_rep[r["NAME"]] = r["REP"]
    elif k == "item":
        item_month.append({"it": r["NAME"], "cat": categorize(r["NAME"]), "m": m,
                           "rev": round(f(r["SALES"]), 2), "cost": round(f(r["COST"]), 2), "cs": round(f(r["CASES"]), 1)})
    elif k == "custgp":
        custgp_month.append({"c": r["NAME"], "m": m,
                             "rev": round(f(r["SALES"]), 2), "cost": round(f(r["COST"]), 2)})

months_cust = sorted({r["m"] for r in cust_month})
months_item = sorted({r["m"] for r in item_month})
all_months = sorted(set(months_cust) | set(months_item))

# ---------- promo (fixed recent window, unchanged) ----------
items = [{"item": r["ITEM"], "buyers": i(r["BUYERS"]), "spend": f(r["SPEND"]),
          "cases": f(r["CASES"]), "avg_case_price": f(r["AVG_CASE_PRICE"]),
          "buyer_list": r["BUYER_LIST"] or ""} for r in items_raw]
today = datetime.date.fromisoformat(cfg.get("as_of", datetime.date.today().isoformat()))
win = cfg.get("active_window_days", 90)
def pd(s):
    try: return datetime.date.fromisoformat(s)
    except Exception: return None
active_custs = {c["customer"]: c["item_spend"] for c in icust
                if pd(c.get("last_item_order")) and (today - pd(c["last_item_order"])).days <= win and c.get("item_spend", 0) > 0}
N = len(active_custs)
hero_min = cfg.get("hero_min_buyers", 8)
hero = sorted([it for it in items if it["buyers"] >= hero_min and it["cases"] > 0],
              key=lambda x: (-x["buyers"], -x["spend"]))
promo_by_item = []
for it in hero:
    buyers = set(it["buyer_list"].split("|")) if it["buyer_list"] else set()
    targets = sorted([(c, active_custs[c]) for c in active_custs if c not in buyers], key=lambda x: -x[1])
    if not targets: continue
    promo_by_item.append({"item": it["item"], "category": categorize(it["item"]),
        "buyers": it["buyers"], "penetration": round(100*it["buyers"]/N) if N else 0,
        "spend": round(it["spend"]), "cases": round(it["cases"]),
        "avg_case_price": round(it["avg_case_price"], 2), "n_targets": len(targets),
        "targets": [{"customer": c, "size": round(s)} for c, s in targets[:12]]})
promo_by_item.sort(key=lambda x: (-x["penetration"], -x["spend"]))
promo_by_customer = []
for cust, size in sorted(active_custs.items(), key=lambda x: -x[1]):
    gaps = []
    for it in hero:
        buyers = set(it["buyer_list"].split("|")) if it["buyer_list"] else set()
        if cust not in buyers: gaps.append(it)
    promo_by_customer.append({"customer": cust, "size": round(size),
        "gaps": [{"item": g["item"], "category": categorize(g["item"]),
                  "penetration": round(100*g["buyers"]/N) if N else 0,
                  "avg_case_price": round(g["avg_case_price"], 2)} for g in gaps[:8]]})

# overall GP (item window)
tot_rev = sum(r["rev"] for r in item_month)
tot_cost = sum(r["cost"] for r in item_month)

payload = {
    "customer_name": cfg["customer_name"],
    "generated_at": datetime.datetime.now().strftime("%B %d, %Y"),
    "as_of": today.isoformat(),
    "months_cust": months_cust, "months_item": months_item, "all_months": all_months,
    "cust_month": cust_month, "item_month": item_month, "custgp_month": custgp_month,
    "cust_rep": cust_rep,
    "gp_overall": {"rev": round(tot_rev), "cost": round(tot_cost),
                   "gp": round(tot_rev - tot_cost),
                   "gp_pct": round(100*(tot_rev - tot_cost)/tot_rev, 1) if tot_rev else 0},
    "cost_note": "Gross profit uses each item's current catalog floor cost applied to volume ordered. Item-level detail (and therefore GP and categories) begins June 2026.",
    "promo": {"universe": N, "hero_min_buyers": hero_min,
              "by_item": promo_by_item, "by_customer": promo_by_customer},
}
with open(os.path.join(HERE, "data.json"), "w") as fh:
    json.dump(payload, fh, separators=(",", ":"))

# ---- receipt / gates ----
tot_sales = sum(r["s"] for r in cust_month)
custs = len({r["c"] for r in cust_month if r["c"] != "Employee"})
cats = collections.Counter()
for r in item_month: cats[r["cat"]] += r["rev"]
uncat = round(100*cats.get("Other / Uncategorized",0)/sum(cats.values()),1)
print(f"cust_month={len(cust_month)} item_month={len(item_month)} custgp_month={len(custgp_month)}")
print(f"total invoice sales=${round(tot_sales):,}  customers={custs}  months {all_months[0]}..{all_months[-1]}")
print(f"GP: rev=${round(tot_rev):,} cost=${round(tot_cost):,} GP={payload['gp_overall']['gp_pct']}%  uncat={uncat}%")
print(f"promo N={N} hero={len(promo_by_item)}")
assert abs(tot_sales-527701) < 300, f"sales drift {tot_sales}"
assert 0 < payload['gp_overall']['gp_pct'] < 40
print("OK -> data.json")
