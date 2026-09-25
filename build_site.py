#!/usr/bin/env python3
"""Encrypt data.json (PBKDF2 + AES-GCM) into a self-contained, password-gated
index.html with a date-range filter and real gross-profit reports. Decryption
happens in the viewer's browser via WebCrypto; no server needed."""
import json, os, base64, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "config.json")))
plaintext = open(os.path.join(HERE, "data.json"), "rb").read()
ITER = 200000
salt = os.urandom(16); iv = os.urandom(12)
key = hashlib.pbkdf2_hmac("sha256", cfg["password"].encode(), salt, ITER, dklen=32)
ct = AESGCM(key).encrypt(iv, plaintext, None)
b64 = lambda b: base64.b64encode(b).decode()

HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>__CUSTOMER__ · Reporting</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#f4f6f8;--card:#fff;--ink:#12232e;--muted:#5b6b76;--line:#e3e8ec;--accent:#0b6b5f;
 --accent2:#0e8a79;--chip:#eef3f2;--bar:#0e8a79;--bar2:#c9d6d3;--warn-bg:#fff6e6;--warn-ink:#8a5a00;
 --warn-line:#f0d9a8;--pos:#0e8a79;--neg:#c0392b}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0e1518;--card:#15201f;
 --ink:#e8eeec;--muted:#9fb0ab;--line:#243230;--accent:#2bb39c;--accent2:#37c9af;--chip:#1c2a28;
 --bar:#2bb39c;--bar2:#2a3a37;--warn-bg:#2a2213;--warn-ink:#e9c877;--warn-line:#4a3d1c;--pos:#37c9af;--neg:#e6785f}}
:root[data-theme="dark"]{--bg:#0e1518;--card:#15201f;--ink:#e8eeec;--muted:#9fb0ab;--line:#243230;
 --accent:#2bb39c;--accent2:#37c9af;--chip:#1c2a28;--bar:#2bb39c;--bar2:#2a3a37;--warn-bg:#2a2213;
 --warn-ink:#e9c877;--warn-line:#4a3d1c;--pos:#37c9af;--neg:#e6785f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.45}
.wrap{max-width:1160px;margin:0 auto;padding:0 16px}
#gate{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px}
#gate .box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:32px;max-width:400px;width:100%;box-shadow:0 8px 40px rgba(0,0,0,.08)}
#gate h1{font-size:20px;margin:0 0 4px}#gate p{color:var(--muted);font-size:14px;margin:0 0 20px}
#gate input{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font-size:16px}
#gate button{width:100%;margin-top:12px;padding:12px;border:0;border-radius:10px;background:var(--accent);color:#fff;font-size:15px;font-weight:600;cursor:pointer}
#gate .err{color:#d9534f;font-size:13px;margin-top:10px;min-height:16px}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.5px;color:var(--accent);background:var(--chip);padding:4px 10px;border-radius:999px;margin-bottom:14px}
header{background:var(--card);border-bottom:1px solid var(--line);padding:16px 0;position:sticky;top:0;z-index:10}
header .row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
header h1{font-size:19px;margin:0}header .sub{color:var(--muted);font-size:13px;margin-top:2px}
#logout{font-size:12px;background:none;border:1px solid var(--line);color:var(--muted);padding:6px 10px;border-radius:8px;cursor:pointer}
.filterbar{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:18px 0;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.filterbar label{font-size:12px;color:var(--muted);font-weight:600}
.filterbar input[type=month]{padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font-size:13px}
.presets{display:flex;gap:6px;flex-wrap:wrap}
.preset{font-size:12px;padding:6px 11px;border:1px solid var(--line);border-radius:999px;background:var(--bg);color:var(--muted);cursor:pointer;font-weight:600}
.preset.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.rangenote{font-size:12px;color:var(--muted);margin-left:auto}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .v{font-size:23px;font-weight:700}.kpi .l{font-size:12px;color:var(--muted);margin-top:2px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 8px}
.tab{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap}
.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.panel{display:none;margin:8px 0 60px}.panel.active{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px}
.card h2{font-size:16px;margin:0 0 4px}.card .desc{color:var(--muted);font-size:13px;margin:0 0 14px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--muted);font-weight:600;font-size:11px;letter-spacing:.4px;text-transform:uppercase;cursor:pointer;user-select:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:hover{background:var(--chip)}
.search{width:100%;max-width:320px;padding:9px 12px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);font-size:14px;margin-bottom:12px}
.bar{height:8px;border-radius:6px;background:var(--bar);display:inline-block;vertical-align:middle}
.barwrap{background:var(--bar2);border-radius:6px;height:8px;width:120px;display:inline-block;vertical-align:middle;overflow:hidden}
.tag{display:inline-block;font-size:11px;background:var(--chip);color:var(--muted);padding:2px 8px;border-radius:6px}
.pos{color:var(--pos)}.neg{color:var(--neg)}
.callout{background:var(--warn-bg);border:1px solid var(--warn-line);color:var(--warn-ink);border-radius:10px;padding:14px 16px;font-size:13px;margin-bottom:16px}
.subtabs{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.subtab{padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--muted);font-size:12px;font-weight:600;cursor:pointer}
.subtab.active{background:var(--accent2);color:#fff;border-color:var(--accent2)}
.promo-item{border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px}
.promo-item .head{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:baseline}
.promo-item .name{font-weight:700;font-size:14px}.promo-item .why{font-size:12px;color:var(--muted);margin:6px 0 10px}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chips .c{font-size:12px;background:var(--chip);border-radius:999px;padding:4px 10px}
.foot{color:var(--muted);font-size:12px;text-align:center;padding:26px 0 40px}
.repcard{border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.repcard .rt{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}.repcard .rn{font-size:16px;font-weight:700}
.mini{display:grid;grid-template-columns:repeat(auto-fit,minmax(85px,1fr));gap:10px;margin:12px 0}
.mini .mv{font-size:17px;font-weight:700}.mini .ml{font-size:11px;color:var(--muted)}
canvas{max-width:100%}
@media(max-width:640px){.hide-sm{display:none}.kpi .v{font-size:19px}.rangenote{margin-left:0;width:100%}}
</style></head><body>
<div id="gate"><div class="box">
  <div class="badge">AYS · PEPPER REPORTING</div>
  <h1>__CUSTOMER__ Reporting</h1>
  <p>Enter the password to view your live sales dashboard.</p>
  <input id="pw" type="password" placeholder="Password" autocomplete="current-password" autofocus>
  <button id="go">View dashboard</button><div class="err" id="err"></div>
</div></div>

<div id="app" style="display:none">
<header><div class="wrap row">
  <div><h1>__CUSTOMER__ · Reporting</h1><div class="sub">Powered by Pepper · updated <span id="gen"></span></div></div>
  <button id="logout">Lock</button>
</div></header>
<div class="wrap">
  <div class="filterbar">
    <div><label>From</label><br><input type="month" id="from"></div>
    <div><label>To</label><br><input type="month" id="to"></div>
    <div class="presets" id="presets"></div>
    <div class="rangenote" id="rangenote"></div>
  </div>
  <div class="kpis" id="kpis"></div>
  <div class="tabs" id="tabs"></div>
  <div class="panel" id="p-overview"></div>
  <div class="panel" id="p-sales"></div>
  <div class="panel" id="p-cases"></div>
  <div class="panel" id="p-reps"></div>
  <div class="panel" id="p-cats"></div>
  <div class="panel" id="p-gp"></div>
  <div class="panel" id="p-promo"></div>
  <div class="foot">AYS Distributors reporting · invoiced Pepper orders · gross profit at current catalog floor cost · Powered by Pepper</div>
</div></div>

<script>
const ENC={salt:"__SALT__",iv:"__IV__",ct:"__CT__",iter:__ITER__};
const b64d=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
let DATA=null, RF=null, RT=null, CURTAB="overview", trendChart=null, repChart=null;
const $=s=>document.querySelector(s);
const money=n=>(n<0?"-$":"$")+Math.abs(Math.round(n)).toLocaleString();
const cnum=n=>Math.round(n).toLocaleString();
const pct=n=>(Math.round(n*10)/10)+"%";

async function decrypt(pw){
  const enc=new TextEncoder();
  const km=await crypto.subtle.importKey("raw",enc.encode(pw),"PBKDF2",false,["deriveKey"]);
  const key=await crypto.subtle.deriveKey({name:"PBKDF2",salt:b64d(ENC.salt),iterations:ENC.iter,hash:"SHA-256"},
    km,{name:"AES-GCM",length:256},false,["decrypt"]);
  const pt=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64d(ENC.iv)},key,b64d(ENC.ct));
  return JSON.parse(new TextDecoder().decode(pt));
}
$("#go").onclick=tryUnlock;
$("#pw").addEventListener("keydown",e=>{if(e.key==="Enter")tryUnlock();});
async function tryUnlock(){const pw=$("#pw").value;$("#err").textContent="";$("#go").disabled=true;
  try{DATA=await decrypt(pw);try{sessionStorage.setItem("ays_pw",pw);}catch(e){}boot();
    $("#gate").style.display="none";$("#app").style.display="block";}
  catch(e){$("#err").textContent="Incorrect password.";$("#go").disabled=false;}}
$("#logout").onclick=()=>{try{sessionStorage.removeItem("ays_pw");}catch(e){}location.reload();};
(async()=>{try{const p=sessionStorage.getItem("ays_pw");if(p){DATA=await decrypt(p);boot();
  $("#gate").style.display="none";$("#app").style.display="block";}}catch(e){}})();

const TABS=[["overview","Overview"],["sales","Sales by Customer"],["cases","Cases by Customer"],
  ["reps","Sales by Rep"],["cats","Categories"],["gp","Gross Profit"],["promo","Promo Opportunities"]];

function boot(){
  $("#gen").textContent=DATA.generated_at;
  const m=DATA.all_months, first=m[0], last=m[m.length-1];
  $("#from").min=first;$("#from").max=last;$("#to").min=first;$("#to").max=last;
  RF=first;RT=last;$("#from").value=RF;$("#to").value=RT;
  $("#from").onchange=()=>{RF=$("#from").value;clampPreset();renderAll();};
  $("#to").onchange=()=>{RT=$("#to").value;clampPreset();renderAll();};
  const P=[["All time","all"],["Last 3 mo","3"],["Last 6 mo","6"],["YTD 2026","ytd"],["This month","tm"],["Last month","lm"]];
  $("#presets").innerHTML=P.map(p=>`<div class="preset" data-p="${p[1]}">${p[0]}</div>`).join("");
  document.querySelectorAll(".preset").forEach(b=>b.onclick=()=>applyPreset(b.dataset.p));
  $("#tabs").innerHTML=TABS.map(t=>`<div class="tab" data-t="${t[0]}">${t[1]}</div>`).join("");
  document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{CURTAB=t.dataset.t;setTab();});
  applyPreset("all");
}
function applyPreset(p){
  const m=DATA.all_months, last=m[m.length-1];
  const shift=(ym,n)=>{let [y,mo]=ym.split("-").map(Number);mo-=n;while(mo<1){mo+=12;y--;}return y+"-"+String(mo).padStart(2,"0");};
  if(p==="all"){RF=m[0];RT=last;}
  else if(p==="3"){RT=last;RF=shift(last,2);}
  else if(p==="6"){RT=last;RF=shift(last,5);}
  else if(p==="ytd"){RT=last;RF="2026-01";}
  else if(p==="tm"){RF=last;RT=last;}
  else if(p==="lm"){RF=shift(last,1);RT=shift(last,1);}
  if(RF<m[0])RF=m[0];
  $("#from").value=RF;$("#to").value=RT;
  document.querySelectorAll(".preset").forEach(b=>b.classList.toggle("active",b.dataset.p===p));
  renderAll();
}
function clampPreset(){if(RF>RT){const t=RF;RF=RT;RT=t;$("#from").value=RF;$("#to").value=RT;}
  document.querySelectorAll(".preset").forEach(b=>b.classList.remove("active"));}
const inRange=m=>m>=RF&&m<=RT;

/* ---------- aggregations for current range ---------- */
function aggCust(){
  const map={};
  DATA.cust_month.forEach(r=>{if(!inRange(r.m))return;
    const o=map[r.c]||(map[r.c]={customer:r.c,rep:r.rep,sales:0,cases:0,orders:0});
    o.sales+=r.s;o.cases+=r.cs;o.orders+=r.o;});
  const a=Object.values(map).filter(c=>c.customer!=="Employee");
  a.forEach(c=>{c.avg_order=c.orders?Math.round(c.sales/c.orders):0;
    c._search=(c.customer+" "+c.rep).toLowerCase();});
  return a;
}
function aggGpCust(){
  const map={};
  DATA.custgp_month.forEach(r=>{if(!inRange(r.m))return;
    const o=map[r.c]||(map[r.c]={customer:r.c,rev:0,cost:0});o.rev+=r.rev;o.cost+=r.cost;});
  const a=Object.values(map);a.forEach(c=>{c.gp=c.rev-c.cost;c.gp_pct=c.rev?100*c.gp/c.rev:0;
    c.rep=DATA.cust_rep[c.customer]||"Direct / Unassigned";c._search=c.customer.toLowerCase();});
  return a;
}
function aggGpItem(){
  const map={};
  DATA.item_month.forEach(r=>{if(!inRange(r.m))return;
    const o=map[r.it]||(map[r.it]={item:r.it,cat:r.cat,rev:0,cost:0,cases:0});
    o.rev+=r.rev;o.cost+=r.cost;o.cases+=r.cs;});
  const a=Object.values(map).filter(x=>x.rev>0);
  a.forEach(x=>{x.gp=x.rev-x.cost;x.gp_pct=x.rev?100*x.gp/x.rev:0;x._search=(x.item+" "+x.cat).toLowerCase();});
  return a;
}
function aggCats(){
  const map={};
  DATA.item_month.forEach(r=>{if(!inRange(r.m))return;
    const o=map[r.cat]||(map[r.cat]={category:r.cat,rev:0,cost:0,cases:0,items:new Set()});
    o.rev+=r.rev;o.cost+=r.cost;o.cases+=r.cs;o.items.add(r.it);});
  const a=Object.values(map);const tot=a.reduce((s,x)=>s+x.rev,0)||1;
  a.forEach(x=>{x.gp=x.rev-x.cost;x.gp_pct=x.rev?100*x.gp/x.rev:0;x.pct=100*x.rev/tot;x.nitems=x.items.size;});
  a.sort((x,y)=>y.rev-x.rev);return a;
}
const itemMonthsInRange=()=>DATA.months_item.some(inRange);

/* ---------- render ---------- */
function setTab(){document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.t===CURTAB));
  document.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));$("#p-"+CURTAB).classList.add("active");}
function renderAll(){
  const custs=aggCust();
  const label=(RF===RT)?RF:(RF+" → "+RT);
  $("#rangenote").textContent="Showing "+label+" · GP & categories cover Jun 2026 onward";
  const sales=custs.reduce((s,c)=>s+c.sales,0), cases=custs.reduce((s,c)=>s+c.cases,0),
    orders=custs.reduce((s,c)=>s+c.orders,0), active=custs.filter(c=>c.sales>0).length;
  const gpc=aggGpCust(); const rev=gpc.reduce((s,c)=>s+c.rev,0), cost=gpc.reduce((s,c)=>s+c.cost,0);
  const gpTile=itemMonthsInRange()?`<div class="kpi"><div class="v">${pct(rev?100*(rev-cost)/rev:0)}</div><div class="l">Gross profit %</div><div class="l">${money(rev-cost)} GP</div></div>`:"";
  $("#kpis").innerHTML=[
    ["Sales",money(sales),orders+" orders"],
    ["Cases",cnum(cases),""],
    ["Customers",cnum(custs.length),active+" active"],
    ["Avg order",money(orders?sales/orders:0),""],
  ].map(x=>`<div class="kpi"><div class="v">${x[1]}</div><div class="l">${x[0]}</div><div class="l">${x[2]}</div></div>`).join("")+gpTile;
  renderOverview(custs);renderSales(custs);renderCases(custs);renderReps(custs);
  renderCats();renderGP();renderPromo();
  setTab();
}

function sortableTable(container,rows,cols,defKey){
  let sortKey=defKey,asc=false,filter="";
  container.innerHTML="";
  const search=document.createElement("input");search.className="search";search.placeholder="Search…";
  search.oninput=()=>{filter=search.value.toLowerCase();draw();};
  const tbl=document.createElement("table");container.appendChild(search);container.appendChild(tbl);
  function draw(){let r=rows.filter(x=>!filter||(x._search||"").includes(filter));
    r.sort((a,b)=>{let va=a[sortKey],vb=b[sortKey];
      if(typeof va==="string")return asc?va.localeCompare(vb):vb.localeCompare(va);return asc?va-vb:vb-va;});
    tbl.innerHTML="<thead><tr>"+cols.map(c=>`<th class="${c.num?'num':''} ${c.hide?'hide-sm':''}" data-k="${c.k}">${c.t}${sortKey===c.k?(asc?" ▲":" ▼"):""}</th>`).join("")+"</tr></thead><tbody>"+
      r.map(x=>"<tr>"+cols.map(c=>`<td class="${c.num?'num':''} ${c.hide?'hide-sm':''} ${c.cls?c.cls(x[c.k]):''}">${c.fmt?c.fmt(x[c.k],x):x[c.k]}</td>`).join("")+"</tr>").join("")+"</tbody>";
    tbl.querySelectorAll("th").forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(k===sortKey)asc=!asc;else{sortKey=k;asc=false;}draw();});}
  draw();
}
const signCls=v=>v<0?"neg":"pos";

function renderOverview(custs){
  const el=$("#p-overview");
  el.innerHTML=`<div class="card"><h2>Monthly sales & cases</h2>
    <div class="desc">Invoiced Pepper orders by month (full history; the shaded range is your current filter).</div>
    <canvas id="trend" height="110"></canvas></div>
   <div class="card"><h2>Top 10 customers — ${RF===RT?RF:RF+" to "+RT}</h2>
    <div class="desc">By invoiced sales in the selected range.</div><div id="ovtop"></div></div>`;
  const top=[...custs].sort((a,b)=>b.sales-a.sales).slice(0,10);const max=(top[0]||{}).sales||1;
  $("#ovtop").innerHTML=`<table><tbody>`+top.map(c=>`<tr><td>${c.customer}</td>
    <td class="hide-sm">${c.rep}</td>
    <td class="num" style="width:150px"><span class="barwrap"><span class="bar" style="width:${Math.round(100*c.sales/max)}%"></span></span></td>
    <td class="num">${money(c.sales)}</td></tr>`).join("")+`</tbody></table>`;
  const ink=getComputedStyle(document.body).getPropertyValue('--muted');
  const grid=getComputedStyle(document.body).getPropertyValue('--line');
  const m=DATA.all_months;
  const cm={},ccm={};m.forEach(x=>{cm[x]=0;ccm[x]=0;});
  DATA.cust_month.forEach(r=>{if(r.c==="Employee")return;cm[r.m]=(cm[r.m]||0)+r.s;ccm[r.m]=(ccm[r.m]||0)+r.cs;});
  const inr=m.map(x=>inRange(x));
  if(trendChart)trendChart.destroy();
  trendChart=new Chart($("#trend"),{data:{labels:m,datasets:[
    {type:"bar",label:"Sales ($)",data:m.map(x=>Math.round(cm[x])),yAxisID:"y",borderRadius:4,
      backgroundColor:m.map((x,i)=>inr[i]?"#0e8a79":"#c9d6d3")},
    {type:"line",label:"Cases",data:m.map(x=>Math.round(ccm[x])),borderColor:"#e0a800",backgroundColor:"#e0a800",yAxisID:"y1",tension:.3,pointRadius:2}
   ]},options:{responsive:true,interaction:{mode:"index",intersect:false},
    plugins:{legend:{labels:{color:ink,boxWidth:12}}},
    scales:{x:{ticks:{color:ink},grid:{display:false}},
     y:{position:"left",ticks:{color:ink,callback:v=>"$"+(v/1000)+"k"},grid:{color:grid}},
     y1:{position:"right",ticks:{color:ink},grid:{display:false}}}}});
}
function renderSales(custs){
  $("#p-sales").innerHTML=`<div class="card"><h2>Sales per customer</h2>
    <div class="desc">Invoiced sales in the selected range. Click a column to sort.</div><div id="salestbl"></div></div>`;
  sortableTable($("#salestbl"),custs,[
    {k:"customer",t:"Customer"},{k:"rep",t:"Rep",hide:true},
    {k:"sales",t:"Sales",num:true,fmt:money},{k:"orders",t:"Orders",num:true},
    {k:"avg_order",t:"Avg order",num:true,fmt:money,hide:true},{k:"cases",t:"Cases",num:true,fmt:cnum,hide:true},
  ],"sales");
}
function renderCases(custs){
  $("#p-cases").innerHTML=`<div class="card"><h2>Cases per customer</h2>
    <div class="desc">Invoiced cases in the selected range.</div><div id="casestbl"></div></div>`;
  custs.forEach(c=>c.cpo=c.orders?Math.round(c.cases/c.orders*10)/10:0);
  sortableTable($("#casestbl"),custs,[
    {k:"customer",t:"Customer"},{k:"rep",t:"Rep",hide:true},
    {k:"cases",t:"Cases",num:true,fmt:cnum},{k:"cpo",t:"Cases/order",num:true,hide:true},
    {k:"orders",t:"Orders",num:true},{k:"sales",t:"Sales",num:true,fmt:money,hide:true},
  ],"cases");
}
function renderReps(custs){
  const map={};custs.forEach(c=>{const o=map[c.rep]||(map[c.rep]={rep:c.rep,sales:0,cases:0,orders:0,custs:0,active:0,top:[]});
    o.sales+=c.sales;o.cases+=c.cases;o.orders+=c.orders;o.custs++;if(c.sales>0)o.active++;o.top.push(c);});
  const reps=Object.values(map).sort((a,b)=>b.sales-a.sales);
  let h=`<div class="callout">Big self-serve accounts (Russell's, Hot Fish Club, Graham's Landing) order directly through the app and aren't tied to a rep — they show under <b>Direct / Unassigned</b>.</div>`;
  reps.forEach(r=>{r.top.sort((a,b)=>b.sales-a.sales);
    h+=`<div class="repcard"><div class="rt"><div class="rn">${r.rep}</div><div class="tag">${r.custs} customers · ${r.active} active</div></div>
     <div class="mini"><div><div class="mv">${money(r.sales)}</div><div class="ml">Sales</div></div>
      <div><div class="mv">${cnum(r.cases)}</div><div class="ml">Cases</div></div>
      <div><div class="mv">${cnum(r.orders)}</div><div class="ml">Orders</div></div></div>
     <table><thead><tr><th>Top customers</th><th class="num">Sales</th></tr></thead><tbody>`+
     r.top.slice(0,8).map(c=>`<tr><td>${c.customer}</td><td class="num">${money(c.sales)}</td></tr>`).join("")+`</tbody></table></div>`;});
  h+=`<div class="card"><h2>Monthly sales by rep</h2><canvas id="reptrend" height="110"></canvas></div>`;
  $("#p-reps").innerHTML=h;
  const ink=getComputedStyle(document.body).getPropertyValue('--muted');
  const grid=getComputedStyle(document.body).getPropertyValue('--line');
  const m=DATA.all_months.filter(inRange);
  const reps2={};DATA.cust_month.forEach(r=>{if(!inRange(r.m)||r.c==="Employee")return;
    (reps2[r.rep]=reps2[r.rep]||{})[r.m]=(reps2[r.rep]?.[r.m]||0)+r.s;});
  const pal={"Jason Keller":"#0e8a79","Direct / Unassigned":"#8aa0a0","Steve Pietracatello":"#e0a800"};
  const ds=Object.keys(reps2).map(rep=>({label:rep,data:m.map(x=>Math.round(reps2[rep][x]||0)),backgroundColor:pal[rep]||"#5b6b76",borderRadius:3,stack:"s"}));
  if(repChart)repChart.destroy();
  repChart=new Chart($("#reptrend"),{type:"bar",data:{labels:m,datasets:ds},
    options:{responsive:true,plugins:{legend:{labels:{color:ink,boxWidth:12}}},
     scales:{x:{stacked:true,ticks:{color:ink},grid:{display:false}},
      y:{stacked:true,ticks:{color:ink,callback:v=>"$"+(v/1000)+"k"},grid:{color:grid}}}}});
}
function renderCats(){
  const el=$("#p-cats");
  if(!itemMonthsInRange()){el.innerHTML=`<div class="callout">No item-level detail before <b>June 2026</b>, so categories aren't available for this date range. Widen the range to include Jun 2026 or later.</div>`;return;}
  const c=aggCats();const max=(c[0]||{}).rev||1;
  el.innerHTML=`<div class="card"><h2>Sales & gross profit by category</h2>
    <div class="desc">Item-level, ${RF===RT?RF:RF+" to "+RT}. AYS has no category field mapped in the source data, so these are <b>derived from item names</b> by Pepper — refine anytime. GP uses current floor cost.</div>
    <table><thead><tr><th>Category</th><th></th><th class="num">Sales</th><th class="num">% sales</th>
     <th class="num">GP $</th><th class="num">GP %</th><th class="num hide-sm">Cases</th><th class="num hide-sm">Items</th></tr></thead><tbody>`+
    c.map(x=>`<tr><td>${x.category}</td>
     <td class="num" style="width:130px"><span class="barwrap"><span class="bar" style="width:${Math.round(100*x.rev/max)}%"></span></span></td>
     <td class="num">${money(x.rev)}</td><td class="num">${pct(x.pct)}</td>
     <td class="num ${signCls(x.gp)}">${money(x.gp)}</td><td class="num ${signCls(x.gp)}">${pct(x.gp_pct)}</td>
     <td class="num hide-sm">${cnum(x.cases)}</td><td class="num hide-sm">${x.nitems}</td></tr>`).join("")+`</tbody></table></div>`;
}
function renderGP(){
  const el=$("#p-gp");
  if(!itemMonthsInRange()){el.innerHTML=`<div class="callout">Gross profit needs item-level cost, which begins <b>June 2026</b>. Widen the date range to include Jun 2026 or later to see GP.</div>`;return;}
  const gc=aggGpCust(),gi=aggGpItem();
  const rev=gc.reduce((s,x)=>s+x.rev,0),cost=gc.reduce((s,x)=>s+x.cost,0),gp=rev-cost;
  el.innerHTML=`
   <div class="callout">Gross profit is computed from each item's <b>current catalog floor cost</b> (the cost you see in PMC) applied to the volume ordered. Reflects item-level orders from <b>Jun 2026 onward</b> that fall within your selected range. Blended GP: <b>${money(gp)} on ${money(rev)} (${pct(rev?100*gp/rev:0)})</b>.</div>
   <div class="subtabs">
     <div class="subtab active" data-s="cust">By customer</div>
     <div class="subtab" data-s="item">By item</div>
     <div class="subtab" data-s="rep">By rep</div>
   </div>
   <div id="gp-cust"></div><div id="gp-item" style="display:none"></div><div id="gp-rep" style="display:none"></div>`;
  // by customer
  const cc=document.createElement("div");$("#gp-cust").appendChild(Object.assign(document.createElement("div"),{className:"card"}));
  $("#gp-cust").innerHTML=`<div class="card"><h2>Gross profit by customer</h2><div class="desc">Revenue, cost and margin per customer.</div><div id="gpcusttbl"></div></div>`;
  sortableTable($("#gpcusttbl"),gc,[
    {k:"customer",t:"Customer"},{k:"rep",t:"Rep",hide:true},
    {k:"rev",t:"Sales",num:true,fmt:money},{k:"cost",t:"Cost",num:true,fmt:money,hide:true},
    {k:"gp",t:"GP $",num:true,fmt:money,cls:signCls},{k:"gp_pct",t:"GP %",num:true,fmt:pct,cls:signCls},
  ],"rev");
  // by item
  $("#gp-item").innerHTML=`<div class="card"><h2>Gross profit by item</h2><div class="desc">Sort by GP % ascending to find low- or negative-margin items to reprice.</div><div id="gpitemtbl"></div></div>`;
  sortableTable($("#gpitemtbl"),gi,[
    {k:"item",t:"Item"},{k:"cat",t:"Category",hide:true},
    {k:"rev",t:"Sales",num:true,fmt:money},{k:"cases",t:"Cases",num:true,fmt:cnum,hide:true},
    {k:"gp",t:"GP $",num:true,fmt:money,cls:signCls},{k:"gp_pct",t:"GP %",num:true,fmt:pct,cls:signCls},
  ],"rev");
  // by rep
  const rmap={};gc.forEach(c=>{const o=rmap[c.rep]||(rmap[c.rep]={rep:c.rep,rev:0,cost:0});o.rev+=c.rev;o.cost+=c.cost;});
  const gr=Object.values(rmap);gr.forEach(x=>{x.gp=x.rev-x.cost;x.gp_pct=x.rev?100*x.gp/x.rev:0;x._search=x.rep.toLowerCase();});
  $("#gp-rep").innerHTML=`<div class="card"><h2>Gross profit by rep</h2><div class="desc">Margin dollars each rep's book is generating.</div><div id="gpreptbl"></div></div>`;
  sortableTable($("#gpreptbl"),gr,[
    {k:"rep",t:"Rep"},{k:"rev",t:"Sales",num:true,fmt:money},{k:"cost",t:"Cost",num:true,fmt:money,hide:true},
    {k:"gp",t:"GP $",num:true,fmt:money,cls:signCls},{k:"gp_pct",t:"GP %",num:true,fmt:pct,cls:signCls},
  ],"gp");
  el.querySelectorAll(".subtab").forEach(s=>s.onclick=()=>{el.querySelectorAll(".subtab").forEach(x=>x.classList.toggle("active",x===s));
    $("#gp-cust").style.display=s.dataset.s==="cust"?"block":"none";
    $("#gp-item").style.display=s.dataset.s==="item"?"block":"none";
    $("#gp-rep").style.display=s.dataset.s==="rep"?"block":"none";});
}
function renderPromo(){
  const el=$("#p-promo");
  el.innerHTML=`<div class="callout">Each product below is <b>popular across AYS's other customers</b> but the listed accounts <b>aren't buying it yet</b> — a natural promo target. Based on the last ${DATA.promo.universe? '90 days of':''} activity across your <b>${DATA.promo.universe}</b> active customers (this view isn't affected by the date filter above). Ranked by how widely the item already sells and its dollar velocity.</div>
   <div class="subtabs"><div class="subtab active" data-s="item">By product (who to target)</div><div class="subtab" data-s="cust">By customer (what they're missing)</div></div>
   <div id="promo-item"></div><div id="promo-cust" style="display:none"></div>`;
  $("#promo-item").innerHTML=`<div class="card"><h2>Top promo products & target lists</h2>
    <div class="desc">Run a one-time promo on the item to the customers shown; once they order it, it enters their order guide.</div>`+
    DATA.promo.by_item.map(p=>`<div class="promo-item"><div class="head"><div class="name">${p.item}</div><div class="tag">${p.category}</div></div>
     <div class="why">Bought by <b>${p.buyers} of ${DATA.promo.universe}</b> active customers (${p.penetration}%) · ${money(p.spend)} across the book · ~${money(p.avg_case_price)}/case · <b>${p.n_targets}</b> not buying it</div>
     <div class="chips">${p.targets.map(t=>`<span class="c">${t.customer} <span style="color:var(--muted)">${money(t.size)}</span></span>`).join("")}</div></div>`).join("")+`</div>`;
  $("#promo-cust").innerHTML=`<div class="card"><h2>Popular products each customer is missing</h2>
    <div class="desc">Percent = how widely the item sells across AYS. High % = a safe bet this customer would buy it too.</div>`+
    DATA.promo.by_customer.map(c=>`<div class="promo-item"><div class="head"><div class="name">${c.customer}</div><div class="tag">${money(c.size)} active spend</div></div>
     <div class="chips" style="margin-top:8px">${c.gaps.map(g=>`<span class="c">${g.item} <span style="color:var(--muted)">${g.penetration}%</span></span>`).join("")}</div></div>`).join("")+`</div>`;
  el.querySelectorAll(".subtab").forEach(s=>s.onclick=()=>{el.querySelectorAll(".subtab").forEach(x=>x.classList.toggle("active",x===s));
    $("#promo-item").style.display=s.dataset.s==="item"?"block":"none";$("#promo-cust").style.display=s.dataset.s==="cust"?"block":"none";});
}
</script></body></html>"""

out=(HTML.replace("__CUSTOMER__",cfg["customer_name"]).replace("__SALT__",b64(salt))
     .replace("__IV__",b64(iv)).replace("__CT__",b64(ct)).replace("__ITER__",str(ITER)))
with open(os.path.join(HERE,"index.html"),"w") as f: f.write(out)
print(f"index.html written ({len(out):,} bytes)  password='{cfg['password']}'  payload={len(ct):,}B")
