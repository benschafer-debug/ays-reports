# AYS Distributors — Reporting Dashboard

Password-gated public reporting page for AYS Distributors, powered by Pepper (Snowflake).

- Live: https://benschafer-debug.github.io/ays-reports/
- Password protected: the data payload is AES-GCM encrypted (PBKDF2-SHA256) and only
  decrypts in the browser once the correct password is entered. The password lives in
  `config.json` (NOT committed).
- Reports: Overview, Sales/Cases per customer, Sales per rep, Category breakdown,
  Promo opportunities (popular products a customer isn't buying), Gross Profit (pending cost feed).

## Rebuild / refresh
1. Re-pull Snowflake into `raw_customers.json`, `raw_monthly.json`, `raw_icust.json`, `raw_items.json`
2. `python3 make_data.py` → `data.json`
3. `python3 build_site.py` → `index.html`
4. `git add index.html && git commit -m "refresh" && git push`

Only `index.html` (encrypted) is published. `data.json`, the raw pulls, and `config.json`
(password) are gitignored and never leave the machine.
