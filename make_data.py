#!/usr/bin/env python3
"""Transform raw AYS pulls into the report payload (data.json, plaintext).
Inputs (in this dir): raw_customers.json, raw_monthly.json, raw_items.json, raw_icust.json
Output: data.json  (consumed by build_site.py, which encrypts it into index.html)
"""
import json, os, re, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
def load(p):
    with open(os.path.join(HERE, p)) as f:
        return json.load(f)

cfg = load("config.json")
customers = load("raw_customers.json")
monthly   = load("raw_monthly.json")
icust     = load("raw_icust.json")

# raw_items.json is the saved sql tool result (wrapped); find first '{' and parse
with open(os.path.join(HERE, "raw_items.json")) as f:
    _raw = f.read()
_it = json.loads(_raw[_raw.find("{"):])
_cols = [c["name"] for c in _it["result_set"]["resultSetMetaData"]["rowType"]]
items = []
for row in _it["result_set"]["data"]:
    d = dict(zip(_cols, row))
    items.append({
        "item": d["ITEM"],
        "buyers": int(d["BUYERS"]),
        "spend": float(d["SPEND"]),
        "cases": float(d["CASES"]),
        "avg_case_price": float(d["AVG_CASE_PRICE"]) if d["AVG_CASE_PRICE"] not in (None, "") else 0.0,
        "buyer_list": d["BUYER_LIST"] or "",
    })

def num(x):
    return float(x) if x not in (None, "") else 0.0

for c in customers:
    for k in ("sales", "cases", "sales_30d", "sales_90d"):
        c[k] = num(c.get(k))

# ---------- derived category (AYS has no taxonomy; keyword rules) ----------
# ordered rules: first match wins. Tuned to AYS's item naming.
RULES = [
    ("Gloves",              ["glove", "vitrile", "nitrile"]),
    ("Cups & Lids",         ["portion cup", "portion lid", "shot cup", "foam cup", "cup", "lid"]),
    ("To-Go & Containers",  ["to go box", "to go container", "togo", "hinged", "clamshell",
                              "deli container", "foam container", "paper container", "container",
                              "food tray", " tray", "bowl", "plate", "pizza box", "carrier",
                              "steam pan", "foil pan"]),
    ("Napkins",             ["napkin"]),
    ("Wraps, Foil & Film",  ["foil", "film", "deli wrap", "wax paper", "butcher paper",
                              "steak paper", "pan liner", "wrap"]),
    ("Bags & Can Liners",   ["can liner", "liner", "portion bag", "sos bag", "grocery bag",
                              "thank you bag", "bag", "trash"]),
    ("Paper & Register",    ["paper towel", "towel", "tissue", "register roll", "thermal",
                              "bond", "ink ribbon", "guest check", "label", "roll towel"]),
    ("Cutlery & Picks",     ["cutlery", "fork", "knife", "teaspoon", "spoon", "skewer",
                              "toothpick", "pick", "stir straw", "napkin band"]),
    ("Straws",              ["straw"]),
    ("Cleaning & Chemicals",["cleaner", "bleach", "detergent", "sanitiz", "soap", "scrub",
                              "scour", "degreaser", "grill brick", "sponge", "mop", "eraser",
                              "clorox", "pine-sol", "windex", "comet", "griddle screen",
                              "steramine", "n2o"]),
    ("Beverage & Syrups",   ["syrup", "smoothie", "monin", "torani", "grenadine", "juice",
                              "creamer", "tea filter", "milk"]),
    ("Food",                ["food", "sauce", "ketchup", "mayonnaise", "mayo", "cheese",
                              "beef", "shrimp", "crab", "tuna", "sausage", "butter", "margarine",
                              "bun", "bread", "hoagie", "pie", "parfait", "salt", "pepper",
                              "seasoning", "vinegar", "pickle", "okra", "green bean", "asparagus",
                              "potato", "tortilla", "pasta", "linguini", "crackers", "olive",
                              "garlic", "honey", "sriracha", "teriyaki", "soy", "panko", "breader",
                              "dressing", "coleslaw", "custard", "avocado", "cherries", "pollock",
                              "cod", "clam", "andouille", "kielbasa", "bacon", "oil", "soup",
                              "lime", "lemon", "mustard", "hot sauce", "seafood", "roll"]),
]
def categorize(name):
    n = name.lower()
    for cat, kws in RULES:
        for kw in kws:
            if kw in n:
                return cat
    return "Other / Uncategorized"

cat_totals = collections.defaultdict(lambda: {"spend": 0.0, "cases": 0.0, "items": 0, "custs": set()})
for it in items:
    cat = categorize(it["item"])
    it["category"] = cat
    t = cat_totals[cat]
    t["spend"] += it["spend"]; t["cases"] += it["cases"]; t["items"] += 1
    for b in (it["buyer_list"].split("|") if it["buyer_list"] else []):
        t["custs"].add(b)
item_spend_total = sum(it["spend"] for it in items)
categories = []
for cat, t in cat_totals.items():
    categories.append({
        "category": cat, "spend": round(t["spend"]), "cases": round(t["cases"]),
        "items": t["items"], "customers": len(t["custs"]),
        "pct": round(100 * t["spend"] / item_spend_total, 1) if item_spend_total else 0,
    })
categories.sort(key=lambda x: -x["spend"])

# ---------- per-rep rollup ----------
rep_roll = collections.defaultdict(lambda: {"sales": 0.0, "cases": 0.0, "orders": 0, "custs": 0,
                                            "sales_90d": 0.0, "active_90d": 0, "top": []})
for c in customers:
    r = rep_roll[c["rep"]]
    r["sales"] += c["sales"]; r["cases"] += c["cases"]; r["orders"] += c["orders"]
    r["custs"] += 1
    r["sales_90d"] += c["sales_90d"]
    if c["sales_90d"] > 0:
        r["active_90d"] += 1
    r["top"].append((c["customer"], c["sales"]))
reps = []
for name, r in rep_roll.items():
    r["top"].sort(key=lambda x: -x[1])
    reps.append({
        "rep": name, "sales": round(r["sales"]), "cases": round(r["cases"]),
        "orders": r["orders"], "customers": r["custs"], "sales_90d": round(r["sales_90d"]),
        "active_90d": r["active_90d"],
        "top_customers": [{"customer": n, "sales": round(s)} for n, s in r["top"][:8]],
    })
reps.sort(key=lambda x: -x["sales"])

# per-rep monthly (for stacked trend)
rep_month = collections.defaultdict(lambda: collections.defaultdict(float))
all_months = set()
for m in monthly:
    all_months.add(m["month"])
    rep_month[m["rep"]][m["month"]] += num(m.get("sales"))
months_sorted = sorted(all_months)
rep_series = {rep: [round(rep_month[rep].get(mo, 0)) for mo in months_sorted]
              for rep in rep_month}
company_month = [round(sum(rep_month[rep].get(mo, 0) for rep in rep_month)) for mo in months_sorted]
company_cases_month = collections.defaultdict(float)
for m in monthly:
    company_cases_month[m["month"]] += num(m.get("cases"))
company_cases = [round(company_cases_month.get(mo, 0)) for mo in months_sorted]

# ---------- promo opportunities ----------
today = datetime.date.fromisoformat(cfg.get("as_of", datetime.date.today().isoformat()))
win = cfg.get("active_window_days", 90)
def parse_d(s):
    try: return datetime.date.fromisoformat(s)
    except Exception: return None
active_custs = {}
for c in icust:
    d = parse_d(c.get("last_item_order"))
    if d and (today - d).days <= win and c.get("item_spend", 0) > 0:
        active_custs[c["customer"]] = c["item_spend"]
N = len(active_custs)  # promo universe = customers active in item window

hero_min = cfg.get("hero_min_buyers", 8)
hero = [it for it in items if it["buyers"] >= hero_min and it["cases"] > 0]
hero.sort(key=lambda x: (-x["buyers"], -x["spend"]))

# per-item target lists (who ISN'T buying a popular item)
promo_by_item = []
for it in hero:
    buyers = set(it["buyer_list"].split("|")) if it["buyer_list"] else set()
    targets = [(c, active_custs[c]) for c in active_custs if c not in buyers]
    targets.sort(key=lambda x: -x[1])  # biggest active customers first
    if not targets:
        continue
    promo_by_item.append({
        "item": it["item"], "category": it["category"],
        "buyers": it["buyers"], "penetration": round(100 * it["buyers"] / N) if N else 0,
        "spend": round(it["spend"]), "cases": round(it["cases"]),
        "avg_case_price": round(it["avg_case_price"], 2),
        "n_targets": len(targets),
        "targets": [{"customer": c, "size": round(s)} for c, s in targets[:12]],
    })
promo_by_item.sort(key=lambda x: (-x["penetration"], -x["spend"]))

# per-customer gap lists (what popular items is THIS customer missing)
hero_index = {it["item"]: it for it in hero}
promo_by_customer = []
for cust, size in sorted(active_custs.items(), key=lambda x: -x[1]):
    gaps = []
    for it in hero:
        buyers = set(it["buyer_list"].split("|")) if it["buyer_list"] else set()
        if cust not in buyers:
            gaps.append(it)
    gaps.sort(key=lambda x: (-x["buyers"], -x["spend"]))
    promo_by_customer.append({
        "customer": cust, "size": round(size),
        "gaps": [{"item": g["item"], "category": g["category"],
                  "penetration": round(100 * g["buyers"] / N) if N else 0,
                  "avg_case_price": round(g["avg_case_price"], 2),
                  "spend": round(g["spend"])} for g in gaps[:8]],
    })

# ---------- headline KPIs ----------
real_custs = [c for c in customers if c["customer"] not in ("Employee",)]
total_sales = round(sum(c["sales"] for c in real_custs))
total_cases = round(sum(c["cases"] for c in real_custs))
total_orders = sum(c["orders"] for c in real_custs)
active_90 = sum(1 for c in real_custs if c["sales_90d"] > 0)
last90_sales = round(sum(c["sales_90d"] for c in real_custs))

payload = {
    "customer_name": cfg["customer_name"],
    "generated_at": datetime.datetime.now().strftime("%B %d, %Y"),
    "as_of": today.isoformat(),
    "kpis": {
        "total_sales": total_sales, "total_cases": total_cases, "total_orders": total_orders,
        "customers": len(real_custs), "active_90": active_90, "last90_sales": last90_sales,
        "history_start": min(c["first_order"] for c in customers if c.get("first_order")),
    },
    "customers": [{
        "customer": c["customer"], "rep": c["rep"], "orders": c["orders"],
        "sales": round(c["sales"]), "cases": round(c["cases"]),
        "sales_30d": round(c["sales_30d"]), "sales_90d": round(c["sales_90d"]),
        "avg_order": round(c["sales"] / c["orders"]) if c["orders"] else 0,
        "first_order": c["first_order"], "last_order": c["last_order"],
    } for c in sorted(real_custs, key=lambda x: -x["sales"])],
    "reps": reps,
    "months": months_sorted,
    "company_month_sales": company_month,
    "company_month_cases": company_cases,
    "rep_series": rep_series,
    "categories": categories,
    "category_window": {"start": "2026-06", "note": "item-level detail begins June 2026"},
    "promo": {
        "universe": N, "hero_min_buyers": hero_min,
        "by_item": promo_by_item, "by_customer": promo_by_customer,
    },
}

with open(os.path.join(HERE, "data.json"), "w") as f:
    json.dump(payload, f, separators=(",", ":"))

# ---- console receipt / safety gate ----
print(f"customers={len(real_custs)}  total_sales=${total_sales:,}  active_90d={active_90}")
print(f"reps={[(r['rep'], r['sales']) for r in reps]}")
print(f"categories={len(categories)} top={[(c['category'], c['pct']) for c in categories[:6]]}")
uncat = next((c for c in categories if c['category'].startswith('Other')), None)
print(f"uncategorized_pct={uncat['pct'] if uncat else 0}")
print(f"promo universe N={N}  hero_items={len(hero)}  by_item_rows={len(promo_by_item)}")
assert len(real_custs) > 50, "too few customers - aborting"
assert total_sales > 400000, "sales too low - aborting"
print("OK -> data.json")
