let cur;

const closed=new Set(),op=k=>closed.has(k)&&!$("#q").value?"":" open";
const $=s=>document.querySelector(s),E=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])).replace(/↑/g,'<b class="ar up" title="increased">↑</b>').replace(/↓/g,'<b class="ar dn" title="decreased">↓</b>');
const CC={"Antibacterial":["#0072B2","●"],"Antifungal":["#009E73","▲"],"Antiparasitic":["#E69F00","◆"],"Antiviral":["#D55E00","■"],"Gastrointestinal":["#56B4E9","▲"],"Immunomodulator":["#CC79A7","■"],"Hepatobiliary":["#F0E442","◆"],"Analgesic":["#D55E00","▲"],"Antidote":["#009E73","■"],"Antiseizure":["#0072B2","◆"],"Anaesthetic / sedative":["#E69F00","●"],"Bone metabolism":["#56B4E9","◆"],"Respiratory":["#56B4E9","●"],"Antihistamine":["#CC79A7","●"],"Haematological":["#D55E00","◆"], "Cardiovascular":["#D55E00","●"]};
const cc=c=>{if(CC[c])return CC[c];let h=0;for(const ch of c)h=(h*31+ch.charCodeAt(0))>>>0;const P=["#0072B2","#009E73","#E69F00","#D55E00","#56B4E9","#CC79A7","#F0E442"],G=["●","▲","◆","■"];return[P[h%7],G[(h>>3)%4]]};

let DB=[];

const ul=(a,c)=>`<ul>${(a||[]).map(x=>`<li>${E(x)}</li>`).join("")}</ul>`;
const rows=(o,m)=>`<div class="tw"><table>${m.map(([k,l])=>`<tr><th>${l}</th><td>${E(o?.[k]||"—")}</td></tr>`).join("")}</table></div>`;
const RL={avoid:"⛔ AVOID",caution:"⚠ CAUTION",ok:"✓ OK",note:"ℹ NOTE",none:""};

const SK=[["liver","Liver failure"],["kidney","Kidney failure"],["pregnancy","Pregnancy"],["breastfeeding","Breastfeeding"],["allergy","Allergy"],["sex","Sex"],["age","Age"],["genetic","Genetic"]];
function risk(d,k){
 const v=d.sus?.[k]||"—",o=d.sus?.risk?.[k];
 if(o)return o; if(v==="—")return"none";
 if(k==="allergy"||/^avoid|contraindicated/i.test(v))return"avoid";
 if(/caution|↓ dose|↑|monitor|essential|limited/i.test(v))return"caution";
 return SK.slice(0,4).some(x=>x[0]===k)?"ok":"note";
}

const glance=d=>`<div class="glance">${SK.slice(0,4).map(([k,l])=>{const r=risk(d,k);return `<span class="rk ${r}">${RL[r].split(" ")[0]||"–"} ${l}</span>`}).join("")}</div>`;
const susHtml=d=>`<div class="grid">${SK.map(([k,l])=>{const r=risk(d,k);return `<div class="cell ${r}"><div class="rl">${RL[r]} ${l}</div><div class="cb">${E(d.sus?.[k]||"—")}</div></div>`}).join("")}</div>`;
const vf=d=>{const v=d.verified;if(!v)return'<span class="vf no">○ Not yet verified</span>';const t=new Date(v+"T00:00:00"),s=isNaN(t)?E(v):t.toLocaleDateString("en-AU",{day:"numeric",month:"short",year:"numeric"});return`<span class="vf ok">✓ Verified ${s}</span>`};

function show(d){
 $("#main").style.setProperty("--cc",cc(d.cls)[0]);
 $("#main").innerHTML=`<h1>${E(d.name)}</h1><p class="sub">${E(d.brand)} · <span class="cbg">${E(d.family)}</span> › ${E(d.cls)}${d.sub?` › ${E(d.sub)}`:""} · ${vf(d)}</p>${glance(d)}
<h2>Indications</h2><div class="chips">${(d.ind||[]).map(i=>`<span class="chip">${E(i)}</span>`).join("")}</div>
<h2>Pharmacodynamics</h2><div class="flow"><div class="step t"><b>TARGET</b>${E(d.target)}</div><div class="arr">➜</div><div class="step m"><b>MECHANISM</b>${E(d.moa)}</div><div class="arr">➜</div><div class="step r"><b>RESPONSE</b>${E(d.resp)}</div></div>
<h2>Adversities</h2><div class="contra"><b>⛔ Contraindications</b>${ul(d.contra)}</div>
<div style="margin-top:12px"><div class="tier c"><div class="lab">● Common</div>${ul(d.common)}</div><div class="tier s"><div class="lab">▲ Severe</div>${ul(d.severe)}</div><div class="tier l"><div class="lab">■ Lethal</div>${ul(d.lethal)}</div></div>
<h3>Drug interactions</h3><div class="tw"><table><tr><th>Drug</th><th>Mechanism</th></tr>${(d.ddi||[]).map(x=>`<tr><td>${E(x.drug)}</td><td>${E(x.mech)}</td></tr>`).join("")}</table></div>
<h3>Susceptibilities</h3>${susHtml(d)}
<h2>Pharmacokinetics</h2>${rows(d.pk,[["bio","Bioavailability"],["dist","Distribution"],["met","Metabolism"],["t12","Half-life"],["exc","Excretion"]])}
<h2>Regimen</h2>${rows(d.reg,[["dose","Dose"],["route","Route"],["form","Formulation"],["freq","Frequency"],["timing","Timing"],["stop","Stopping rules"]])}
<p class="key">Key: ● common (solid blue) · ▲ severe (dashed orange) · ■ lethal (filled dark). Shape and fill carry the meaning, not hue alone. ⛔ avoid (solid orange-brown) · ⚠ caution (dashed orange) · ✓ OK (blue)</p>`;
 document.title=d.name;
 if(cur!==d.id){scrollTo(0,0);fade()}
 cur=d.id;enhance();
}

function list(){
 const f=$("#q").value.toLowerCase(),T={};
 DB.filter(d=>JSON.stringify([d.name,d.brand,d.family,d.cls,d.sub,d.ind]).toLowerCase().includes(f))
  .sort((a,b)=>(a.family||"").localeCompare(b.family||"")||a.cls.localeCompare(b.cls)||(a.sub||"").localeCompare(b.sub||"")||a.name.localeCompare(b.name))
  .forEach(d=>{((T[d.family||"Other"]??={})[d.cls]??={})[d.sub||""]??=[];T[d.family||"Other"][d.cls][d.sub||""].push(d)});
 const link=d=>`<a href="#${E(d.id)}" data-id="${E(d.id)}">${E(d.name)} <span class="vm ${d.verified?"y":"n"}">${d.verified?"✓":"○"}</span></a>`;
 const n=x=>Array.isArray(x)?x.length:Object.values(x).reduce((s,v)=>s+n(v),0);
 const grp=(k,label,lvl,inner,o)=>`<details${op(k)} data-k="${E(k)}" class="L${lvl}"><summary>${E(label)} <span class="ct">${n(o)}</span></summary>${inner}</details>`;
 $("#list").innerHTML=Object.entries(T).map(([fa,F])=>grp(fa,fa,1,Object.entries(F).map(([c,C])=>grp(fa+"|"+c,c,2,Object.entries(C).map(([s,a])=>s?grp(fa+"|"+c+"|"+s,s,3,a.map(link).join(""),a):a.map(link).join("")).join(""),C)).join(""),F)).join("")||"<p>No matches.</p>";
 route();
}

function route(){const d=DB.find(x=>x.id===location.hash.slice(1))||DB[0];if(!d)return;show(d);document.querySelectorAll("nav a").forEach(a=>a.classList.toggle("on",a.dataset.id===d.id))}

let p=document.querySelector("nav a.on");while(p&&(p=p.parentElement.closest("details")))p.open=true;

function load(arr){DB=arr;try{localStorage.setItem("drugs",JSON.stringify(arr))}catch(e){}list()}

/* fade on drug switch (150 ms, opacity only) */
function fade(){const m=$("#main");m.classList.remove("fade");void m.offsetWidth;m.classList.add("fade")}

/* study mode */
let study=false;try{study=localStorage.getItem("study")==="1"}catch(e){}
$("nav").insertAdjacentHTML("afterbegin",'<div class="tools"><button id="sm" aria-pressed="false"></button><button id="ra">Reveal all</button></div>');
function enhance(){
 document.querySelectorAll("#main .q").forEach(x=>{x.classList.remove("q","rv");x.removeAttribute("tabindex");x.removeAttribute("role")});
 if(!study)return;
 document.querySelectorAll("#main :is(.chip,.glance,.step,.contra,.tier ul,.tw td,.cell .cb)").forEach(x=>{x.classList.add("q");x.tabIndex=0;x.setAttribute("role","button")});
}
function setStudy(on){
 study=on;document.body.classList.toggle("study",on);
 $("#sm").setAttribute("aria-pressed",on);$("#sm").textContent=on?"Study mode: on":"Study mode: off";$("#ra").hidden=!on;
 try{localStorage.setItem("study",on?"1":"0")}catch(e){}
 enhance();
}
$("#sm").onclick=()=>setStudy(!study);
$("#ra").onclick=()=>document.querySelectorAll("#main .q").forEach(x=>x.classList.add("rv"));
$("#main").addEventListener("click",e=>{const q=e.target.closest(".q");if(q)q.classList.toggle("rv")});
$("#main").addEventListener("keydown",e=>{if((e.key==="Enter"||e.key===" ")&&e.target.classList.contains("q")){e.preventDefault();e.target.classList.toggle("rv")}});
setStudy(study);

function pick(){$("#main").innerHTML=`<div class="empty"><h1>Load your database</h1><p>Open this page from the same folder as <b>drugs.json</b> through a local server or web host to load it automatically. Otherwise choose the file here.</p><label class="btn">Choose drugs.json<input type="file" accept=".json" hidden id="fi"></label></div>`;
 $("#fi").onchange=e=>e.target.files[0].text().then(t=>load(JSON.parse(t)))}
 $("#q").oninput=list;addEventListener("hashchange",route);
fetch("drugs.json",{cache:"no-store"}).then(r=>r.json()).then(load).catch(()=>{try{const c=JSON.parse(localStorage.getItem("drugs"));if(c?.length)return load(c)}catch(e){}pick()});

/* sidebar collapse / expand */
$("#q").insertAdjacentHTML("afterend",'<div class="tools"><button id="ca">Collapse all</button><button id="ea">Expand all</button></div>');
$("#ca").onclick=()=>document.querySelectorAll("#list details").forEach(d=>d.open=false);
$("#ea").onclick=()=>document.querySelectorAll("#list details").forEach(d=>d.open=true);
$("#list").addEventListener("toggle",e=>{const k=e.target.dataset?.k;if(!k||$("#q").value)return;e.target.open?closed.delete(k):closed.add(k)},true);