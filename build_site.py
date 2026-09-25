#!/usr/bin/env python3
"""Encrypt data.json with the config password (PBKDF2 + AES-GCM) and emit a
self-contained, password-gated index.html. No server needed; decryption happens
in the viewer's browser via WebCrypto."""
import json, os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "config.json")))
plaintext = open(os.path.join(HERE, "data.json"), "rb").read()

ITER = 200000
salt = os.urandom(16)
iv = os.urandom(12)
key = hashlib.pbkdf2_hmac("sha256", cfg["password"].encode(), salt, ITER, dklen=32)
ct = AESGCM(key).encrypt(iv, plaintext, None)
b64 = lambda b: base64.b64encode(b).decode()

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>__CUSTOMER__ · Reporting</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#f4f6f8; --card:#ffffff; --ink:#12232e; --muted:#5b6b76; --line:#e4e9 ;
  --line:#e3e8ec; --accent:#0b6b5f; --accent2:#0e8a79; --chip:#eef3f2; --bar:#0e8a79;
  --bar2:#c9d6d3; --warn-bg:#fff6e6; --warn-ink:#8a5a00; --warn-line:#f0d9a8;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0e1518; --card:#15201f; --ink:#e8eeec; --muted:#9fb0ab; --line:#243230;
  --accent:#2bb39c; --accent2:#37c9af; --chip:#1c2a28; --bar:#2bb39c; --bar2:#2a3a37;
  --warn-bg:#2a2213; --warn-ink:#e9c877; --warn-line:#4a3d1c;
}}
:root[data-theme="dark"]{
  --bg:#0e1518; --card:#15201f; --ink:#e8eeec; --muted:#9fb0ab; --line:#243230;
  --accent:#2bb39c; --accent2:#37c9af; --chip:#1c2a28; --bar:#2bb39c; --bar2:#2a3a37;
  --warn-bg:#2a2213; --warn-ink:#e9c877; --warn-line:#4a3d1c;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;line-height:1.45}
a{color:var(--accent2)}
.wrap{max-width:1160px;margin:0 auto;padding:0 16px}
/* gate */
#gate{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px}
#gate .box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:32px;max-width:400px;width:100%;box-shadow:0 8px 40px rgba(0,0,0,.08)}
#gate h1{font-size:20px;margin:0 0 4px}
#gate p{color:var(--muted);font-size:14px;margin:0 0 20px}
#gate input{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font-size:16px}
#gate button{width:100%;margin-top:12px;padding:12px;border:0;border-radius:10px;background:var(--accent);color:#fff;font-size:15px;font-weight:600;cursor:pointer}
#gate button:disabled{opacity:.6}
#gate .err{color:#d9534f;font-size:13px;margin-top:10px;min-height:16px}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.5px;color:var(--accent);
  background:var(--chip);padding:4px 10px;border-radius:999px;margin-bottom:14px}
/* header */
header{background:var(--card);border-bottom:1px solid var(--line);padding:18px 0;position:sticky;top:0;z-index:10}
header .row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
header h1{font-size:19px;margin:0}
header .sub{color:var(--muted);font-size:13px;margin-top:2px}
.pill{font-size:12px;color:var(--muted)}
#logout{font-size:12px;background:none;border:1px solid var(--line);color:var(--muted);padding:6px 10px;border-radius:8px;cursor:pointer}
/* kpis */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .v{font-size:24px;font-weight:700}
.kpi .l{font-size:12px;color:var(--muted);margin-top:2px}
/* tabs */
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:18px 0 8px}
.tab{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--card);
  color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap}
.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.panel{display:none;margin:8px 0 60px}
.panel.active{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px}
.card h2{font-size:16px;margin:0 0 4px}
.card .desc{color:var(--muted);font-size:13px;margin:0 0 14px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--muted);font-weight:600;font-size:11px;letter-spacing:.4px;text-transform:uppercase;cursor:pointer;user-select:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:hover{background:var(--chip)}
.search{width:100%;max-width:320px;padding:9px 12px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);font-size:14px;margin-bottom:12px}
.bar{height:8px;border-radius:6px;background:var(--bar);display:inline-block;vertical-align:middle}
.barwrap{background:var(--bar2);border-radius:6px;height:8px;width:120px;display:inline-block;vertical-align:middle;overflow:hidden}
.tag{display:inline-block;font-size:11px;background:var(--chip);color:var(--muted);padding:2px 8px;border-radius:6px}
.callout{background:var(--warn-bg);border:1px solid var(--warn-line);color:var(--warn-ink);border-radius:10px;padding:14px 16px;font-size:13px;margin-bottom:16px}
.callout b{color:var(--warn-ink)}
.subtabs{display:flex;gap:6px;margin-bottom:14px}
.subtab{padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--muted);font-size:12px;font-weight:600;cursor:pointer}
.subtab.active{background:var(--accent2);color:#fff;border-color:var(--accent2)}
.promo-item{border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px;background:var(--card)}
.promo-item .head{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:baseline}
.promo-item .name{font-weight:700;font-size:14px}
.promo-item .why{font-size:12px;color:var(--muted);margin:6px 0 10px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chips .c{font-size:12px;background:var(--chip);border-radius:999px;padding:4px 10px}
.foot{color:var(--muted);font-size:12px;text-align:center;padding:26px 0 40px}
.repcard{border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.repcard .rt{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}
.repcard .rn{font-size:16px;font-weight:700}
.mini{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:10px;margin:12px 0}
.mini div .mv{font-size:18px;font-weight:700}
.mini div .ml{font-size:11px;color:var(--muted)}
canvas{max-width:100%}
@media(max-width:640px){.hide-sm{display:none}.kpi .v{font-size:20px}}
</style>
</head>
<body>
<div id="gate">
  <div class="box">
    <div class="badge">AYS · PEPPER REPORTING</div>
    <h1>__CUSTOMER__ Reporting</h1>
    <p>Enter the password to view your live sales dashboard.</p>
    <input id="pw" type="password" placeholder="Password" autocomplete="current-password" autofocus>
    <button id="go">View dashboard</button>
    <div class="err" id="err"></div>
  </div>
</div>

<div id="app" style="display:none">
<header><div class="wrap row">
  <div>
    <h1>__CUSTOMER__ · Reporting</h1>
    <div class="sub">Powered by Pepper · updated <span id="gen"></span></div>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    <span class="pill" id="asof"></span>
    <button id="logout">Lock</button>
  </div>
</div></header>

<div class="wrap">
  <div class="kpis" id="kpis"></div>
  <div class="tabs" id="tabs"></div>

  <div class="panel" id="p-overview"></div>
  <div class="panel" id="p-sales"></div>
  <div class="panel" id="p-cases"></div>
  <div class="panel" id="p-reps"></div>
  <div class="panel" id="p-cats"></div>
  <div class="panel" id="p-promo"></div>
  <div class="panel" id="p-gp"></div>

  <div class="foot">AYS Distributors reporting · figures from invoiced Pepper orders · Powered by Pepper</div>
</div>
</div>

<script>
const ENC = {salt:"__SALT__", iv:"__IV__", ct:"__CT__", iter:__ITER__};
const b64d = s => Uint8Array.from(atob(s), c=>c.charCodeAt(0));
let DATA = null;

async function decrypt(pw){
  const enc = new TextEncoder();
  const km = await crypto.subtle.importKey("raw", enc.encode(pw), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    {name:"PBKDF2", salt:b64d(ENC.salt), iterations:ENC.iter, hash:"SHA-256"},
    km, {name:"AES-GCM", length:256}, false, ["decrypt"]);
  const pt = await crypto.subtle.decrypt({name:"AES-GCM", iv:b64d(ENC.iv)}, key, b64d(ENC.ct));
  return JSON.parse(new TextDecoder().decode(pt));
}
const $ = s => document.querySelector(s);
const money = n => "$"+Math.round(n).toLocaleString();
const money0 = n => "$"+Math.round(n).toLocaleString();
const cnum = n => Math.round(n).toLocaleString();

$("#go").onclick = tryUnlock;
$("#pw").addEventListener("keydown", e=>{ if(e.key==="Enter") tryUnlock(); });
async function tryUnlock(){
  const pw = $("#pw").value; $("#err").textContent=""; $("#go").disabled=true;
  try{
    DATA = await decrypt(pw);
    try{ sessionStorage.setItem("ays_pw", pw); }catch(e){}
    render();
    $("#gate").style.display="none"; $("#app").style.display="block";
  }catch(e){ $("#err").textContent="Incorrect password."; $("#go").disabled=false; }
}
$("#logout").onclick = ()=>{ try{sessionStorage.removeItem("ays_pw");}catch(e){} location.reload(); };
// auto-unlock within a session
(async()=>{ try{const p=sessionStorage.getItem("ays_pw"); if(p){ DATA=await decrypt(p); render(); $("#gate").style.display="none"; $("#app").style.display="block"; }}catch(e){} })();

const TABS = [
  ["overview","Overview"],["sales","Sales by Customer"],["cases","Cases by Customer"],
  ["reps","Sales by Rep"],["cats","Categories"],["promo","Promo Opportunities"],
  ["gp","Gross Profit"]
];
function setTab(id){
  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active", t.dataset.t===id));
  document.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));
  $("#p-"+id).classList.add("active");
}

function render(){
  $("#gen").textContent = DATA.generated_at;
  $("#asof").textContent = "data as of "+DATA.as_of;
  const k = DATA.kpis;
  $("#kpis").innerHTML = [
    ["Total sales", money(k.total_sales), "since "+k.history_start],
    ["Cases sold", cnum(k.total_cases), "all-time"],
    ["Orders", cnum(k.total_orders), "invoiced"],
    ["Customers", cnum(k.customers), k.active_90+" active (90d)"],
    ["Last 90 days", money(k.last90_sales), "in sales"],
  ].map(x=>`<div class="kpi"><div class="v">${x[1]}</div><div class="l">${x[0]}</div><div class="l">${x[2]}</div></div>`).join("");

  $("#tabs").innerHTML = TABS.map(t=>`<div class="tab" data-t="${t[0]}">${t[1]}</div>`).join("");
  document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>setTab(t.dataset.t));

  renderOverview(); renderSales(); renderCases(); renderReps(); renderCats(); renderPromo(); renderGP();
  setTab("overview");
}

/* ---------- Overview ---------- */
function renderOverview(){
  const el = $("#p-overview");
  el.innerHTML = `
   <div class="card"><h2>Monthly sales & cases</h2>
     <div class="desc">Invoiced Pepper orders by month.</div>
     <canvas id="trend" height="110"></canvas></div>
   <div class="card"><h2>Top 10 customers</h2>
     <div class="desc">By all-time invoiced sales.</div>
     <div id="ovtop"></div></div>`;
  const top = DATA.customers.slice(0,10);
  const max = top[0].sales;
  $("#ovtop").innerHTML = `<table><tbody>`+top.map(c=>`<tr>
     <td>${c.customer}</td>
     <td class="hide-sm">${c.rep}</td>
     <td class="num" style="width:150px"><span class="barwrap"><span class="bar" style="width:${Math.round(100*c.sales/max)}%"></span></span></td>
     <td class="num">${money(c.sales)}</td></tr>`).join("")+`</tbody></table>`;
  const ctx = $("#trend");
  const grid = getComputedStyle(document.body).getPropertyValue('--line');
  const ink = getComputedStyle(document.body).getPropertyValue('--muted');
  new Chart(ctx,{data:{labels:DATA.months,datasets:[
     {type:"bar",label:"Sales ($)",data:DATA.company_month_sales,backgroundColor:"#0e8a79",yAxisID:"y",borderRadius:4},
     {type:"line",label:"Cases",data:DATA.company_month_cases,borderColor:"#e0a800",backgroundColor:"#e0a800",yAxisID:"y1",tension:.3,pointRadius:2}
   ]},options:{responsive:true,interaction:{mode:"index",intersect:false},
     plugins:{legend:{labels:{color:ink,boxWidth:12}}},
     scales:{
       x:{ticks:{color:ink},grid:{display:false}},
       y:{position:"left",ticks:{color:ink,callback:v=>"$"+(v/1000)+"k"},grid:{color:grid}},
       y1:{position:"right",ticks:{color:ink},grid:{display:false}}
     }}});
}

/* ---------- sortable table helper ---------- */
function sortableTable(container, rows, cols, defaultKey){
  let sortKey = defaultKey, asc = false, filter="";
  const wrap = document.createElement("div");
  const search = document.createElement("input");
  search.className="search"; search.placeholder="Search customer or rep…";
  search.oninput = ()=>{ filter=search.value.toLowerCase(); draw(); };
  const tbl = document.createElement("table");
  wrap.appendChild(search); wrap.appendChild(tbl);
  container.appendChild(wrap);
  function draw(){
    let r = rows.filter(x=> !filter || (x._search||"").includes(filter));
    r.sort((a,b)=>{ let va=a[sortKey],vb=b[sortKey];
      if(typeof va==="string"){return asc?va.localeCompare(vb):vb.localeCompare(va);}
      return asc?va-vb:vb-va; });
    tbl.innerHTML = "<thead><tr>"+cols.map(c=>`<th class="${c.num?'num':''} ${c.hide?'hide-sm':''}" data-k="${c.k}">${c.t}${sortKey===c.k?(asc?" ▲":" ▼"):""}</th>`).join("")+"</tr></thead><tbody>"+
      r.map(x=>"<tr>"+cols.map(c=>`<td class="${c.num?'num':''} ${c.hide?'hide-sm':''}">${c.fmt?c.fmt(x[c.k],x):x[c.k]}</td>`).join("")+"</tr>").join("")+"</tbody>";
    tbl.querySelectorAll("th").forEach(th=>th.onclick=()=>{ const k=th.dataset.k;
      if(k===sortKey) asc=!asc; else {sortKey=k; asc=false;} draw(); });
  }
  draw();
}

/* ---------- Sales by customer ---------- */
function renderSales(){
  const el=$("#p-sales"); el.innerHTML=`<div class="card"><h2>Sales per customer</h2>
    <div class="desc">Invoiced sales, all-time. Click a column to sort.</div><div id="salestbl"></div></div>`;
  const rows = DATA.customers.map(c=>({...c,_search:(c.customer+" "+c.rep).toLowerCase()}));
  sortableTable($("#salestbl"),rows,[
    {k:"customer",t:"Customer"},{k:"rep",t:"Rep",hide:true},
    {k:"sales",t:"Sales",num:true,fmt:money},
    {k:"sales_90d",t:"Last 90d",num:true,fmt:money,hide:true},
    {k:"orders",t:"Orders",num:true},
    {k:"avg_order",t:"Avg order",num:true,fmt:money,hide:true},
    {k:"last_order",t:"Last order",hide:true},
  ],"sales");
}
/* ---------- Cases by customer ---------- */
function renderCases(){
  const el=$("#p-cases"); el.innerHTML=`<div class="card"><h2>Cases per customer</h2>
    <div class="desc">Invoiced cases, all-time.</div><div id="casestbl"></div></div>`;
  const rows = DATA.customers.map(c=>({...c,_search:(c.customer+" "+c.rep).toLowerCase(),
     cases_per_order: c.orders? Math.round(c.cases/c.orders*10)/10:0}));
  sortableTable($("#casestbl"),rows,[
    {k:"customer",t:"Customer"},{k:"rep",t:"Rep",hide:true},
    {k:"cases",t:"Cases",num:true,fmt:cnum},
    {k:"cases_per_order",t:"Cases/order",num:true,hide:true},
    {k:"orders",t:"Orders",num:true},
    {k:"sales",t:"Sales",num:true,fmt:money,hide:true},
  ],"cases");
}
/* ---------- Sales by rep ---------- */
function renderReps(){
  const el=$("#p-reps");
  let h = `<div class="callout">Big self-serve accounts (Russell's, Hot Fish Club, Graham's Landing) order directly through the app and aren't tied to a rep — they show under <b>Direct / Unassigned</b>.</div>`;
  DATA.reps.forEach(r=>{
    h += `<div class="repcard"><div class="rt"><div class="rn">${r.rep}</div>
      <div class="tag">${r.customers} customers · ${r.active_90} active (90d)</div></div>
      <div class="mini">
        <div><div class="mv">${money(r.sales)}</div><div class="ml">Total sales</div></div>
        <div><div class="mv">${money(r.sales_90d)}</div><div class="ml">Last 90 days</div></div>
        <div><div class="mv">${cnum(r.cases)}</div><div class="ml">Cases</div></div>
        <div><div class="mv">${cnum(r.orders)}</div><div class="ml">Orders</div></div>
      </div>
      <table><thead><tr><th>Top customers</th><th class="num">Sales</th></tr></thead><tbody>`+
      r.top_customers.map(c=>`<tr><td>${c.customer}</td><td class="num">${money(c.sales)}</td></tr>`).join("")+
      `</tbody></table></div>`;
  });
  h += `<div class="card"><h2>Monthly sales by rep</h2><canvas id="reptrend" height="110"></canvas></div>`;
  el.innerHTML=h;
  const ink=getComputedStyle(document.body).getPropertyValue('--muted');
  const grid=getComputedStyle(document.body).getPropertyValue('--line');
  const palette={"Jason Keller":"#0e8a79","Direct / Unassigned":"#8aa0a0","Steve Pietracatello":"#e0a800"};
  const ds = Object.keys(DATA.rep_series).map(rep=>({label:rep,data:DATA.rep_series[rep],
     backgroundColor:palette[rep]||"#5b6b76",borderRadius:3,stack:"s"}));
  new Chart($("#reptrend"),{type:"bar",data:{labels:DATA.months,datasets:ds},
    options:{responsive:true,plugins:{legend:{labels:{color:ink,boxWidth:12}}},
     scales:{x:{stacked:true,ticks:{color:ink},grid:{display:false}},
             y:{stacked:true,ticks:{color:ink,callback:v=>"$"+(v/1000)+"k"},grid:{color:grid}}}}});
}
/* ---------- Categories ---------- */
function renderCats(){
  const el=$("#p-cats");
  const c=DATA.categories; const max=c[0].spend;
  let rows = c.map(x=>`<tr><td>${x.category}</td>
    <td class="num" style="width:150px"><span class="barwrap"><span class="bar" style="width:${Math.round(100*x.spend/max)}%"></span></span></td>
    <td class="num">${money(x.spend)}</td><td class="num">${x.pct}%</td>
    <td class="num hide-sm">${cnum(x.cases)}</td><td class="num hide-sm">${x.items}</td>
    <td class="num hide-sm">${x.customers}</td></tr>`).join("");
  el.innerHTML=`<div class="card"><h2>Sales by category</h2>
    <div class="desc">${DATA.category_window.note}. AYS has no category field mapped in the source data, so these categories are <b>derived from item names</b> by Pepper — a good directional read, refine anytime.</div>
    <table><thead><tr><th>Category</th><th></th><th class="num">Sales</th><th class="num">% of items sales</th>
      <th class="num hide-sm">Cases</th><th class="num hide-sm">Items</th><th class="num hide-sm">Customers</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
}
/* ---------- Promo opportunities ---------- */
function renderPromo(){
  const el=$("#p-promo");
  el.innerHTML=`
   <div class="callout">Every product below is <b>popular across AYS's other customers</b> but the listed accounts <b>aren't buying it yet</b> — a natural promo target. Ranked by how widely the item already sells (its penetration across your ${DATA.promo.universe} active customers) and its dollar velocity. <b>Margin-based targeting</b> (e.g. "push high-GP items") needs item cost, which isn't in Pepper yet — see the Gross Profit tab.</div>
   <div class="subtabs">
     <div class="subtab active" data-s="item">By product (who to target)</div>
     <div class="subtab" data-s="cust">By customer (what they're missing)</div>
   </div>
   <div id="promo-item"></div><div id="promo-cust" style="display:none"></div>`;
  // by item
  let hi = DATA.promo.by_item.map(p=>`
    <div class="promo-item">
      <div class="head"><div class="name">${p.item}</div>
        <div class="tag">${p.category}</div></div>
      <div class="why">Bought by <b>${p.buyers} of ${DATA.promo.universe}</b> active customers (${p.penetration}% penetration) · ${money(p.spend)} sold across the book · ~${money(p.avg_case_price)}/case · <b>${p.n_targets}</b> customers not buying it</div>
      <div class="chips">${p.targets.map(t=>`<span class="c">${t.customer} <span style="color:var(--muted)">${money(t.size)}</span></span>`).join("")}</div>
    </div>`).join("");
  $("#promo-item").innerHTML = `<div class="card"><h2>Top promo products & target lists</h2>
     <div class="desc">Run a one-time promo on the item to the customers shown; once they order it, it enters their order guide.</div>${hi}</div>`;
  // by customer
  let hc = DATA.promo.by_customer.map(c=>`
    <div class="promo-item"><div class="head"><div class="name">${c.customer}</div>
      <div class="tag">${money(c.size)} active spend</div></div>
      <div class="chips" style="margin-top:8px">${c.gaps.map(g=>`<span class="c">${g.item} <span style="color:var(--muted)">${g.penetration}%</span></span>`).join("")}</div>
    </div>`).join("");
  $("#promo-cust").innerHTML = `<div class="card"><h2>Popular products each customer is missing</h2>
     <div class="desc">Percent = how widely the item sells across AYS. High % = a safe bet this customer would buy it too.</div>${hc}</div>`;
  el.querySelectorAll(".subtab").forEach(s=>s.onclick=()=>{
    el.querySelectorAll(".subtab").forEach(x=>x.classList.toggle("active",x===s));
    $("#promo-item").style.display = s.dataset.s==="item"?"block":"none";
    $("#promo-cust").style.display = s.dataset.s==="cust"?"block":"none";
  });
}
/* ---------- Gross profit ---------- */
function renderGP(){
  const el=$("#p-gp");
  const top=DATA.customers.slice(0,15);
  el.innerHTML=`
   <div class="callout"><b>Gross profit isn't available yet.</b> Pepper knows the <b>price you charge</b> each customer, but not your <b>item cost</b> — that lives in QuickBooks. To light up true GP per customer / per rep, AYS needs a cost feed (a cost column on the catalog, or a QuickBooks cost sync). Once that's in, this tab fills in automatically. In the meantime, <b>sales per customer</b> below is the closest available view.</div>
   <div class="card"><h2>Sales per customer (GP proxy)</h2>
     <div class="desc">Top 15 by invoiced sales. GP column pending cost data.</div>
     <table><thead><tr><th>Customer</th><th class="num">Sales</th><th class="num">Cases</th><th class="num">Est. GP</th></tr></thead>
     <tbody>${top.map(c=>`<tr><td>${c.customer}</td><td class="num">${money(c.sales)}</td>
       <td class="num">${cnum(c.cases)}</td><td class="num" style="color:var(--muted)">— needs cost</td></tr>`).join("")}</tbody></table></div>`;
}
</script>
</body>
</html>"""

out = (HTML
  .replace("__CUSTOMER__", cfg["customer_name"])
  .replace("__SALT__", b64(salt))
  .replace("__IV__", b64(iv))
  .replace("__CT__", b64(ct))
  .replace("__ITER__", str(ITER)))

with open(os.path.join(HERE, "index.html"), "w") as f:
    f.write(out)
print(f"index.html written ({len(out):,} bytes)  password='{cfg['password']}'  encrypted payload={len(ct):,}B")
