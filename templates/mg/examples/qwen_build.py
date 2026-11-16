import re, shutil, os
CSS = r'''
:root{--ground:#06070c;--ink:#f4f5fb;--mute:#9aa0b8;--violet:#7b6cff;--violet2:#b3a8ff;--cyan:#43d3ff;--red:#ff5d73;--green:#3fe0a0;--amber:#ffc35a;--font-display:Inter;--font-mono:"JetBrains Mono"}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:var(--ground)}
#root{position:relative;width:1920px;height:1080px;font-family:var(--font-display);color:var(--ink);overflow:hidden}
.abs{position:absolute}
#bg{left:0;top:0;width:1920px;height:1080px;z-index:0;background:radial-gradient(1200px 700px at 18% 20%,rgba(123,108,255,.28),transparent 60%),radial-gradient(900px 600px at 90% 90%,rgba(67,211,255,.16),transparent 60%),linear-gradient(160deg,#0a0b14,#05060a)}
#grid{left:0;top:0;width:1920px;height:1080px;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:64px 64px}
#cam{left:0;top:0;width:1920px;height:1080px;z-index:5;transform-origin:960px 540px;clip-path:inset(0px 0px 0px 0px round 0px)}
#spk{left:0;top:0;width:1920px;height:1080px;object-fit:cover}
.ring{z-index:6;border-radius:50%;border:4px solid rgba(179,168,255,.9);box-shadow:0 0 40px rgba(123,108,255,.55);opacity:0}
.frame{z-index:6;border:3px solid rgba(179,168,255,.75);box-shadow:0 0 50px rgba(123,108,255,.35);opacity:0}
.scene{left:0;top:0;width:1920px;height:1080px;z-index:2}
.kick{font:700 26px var(--font-mono);letter-spacing:.18em;text-transform:uppercase;color:var(--violet2)}
.h1{font-weight:900;font-size:104px;letter-spacing:-.04em;line-height:.98}
.h2{font-weight:900;font-size:72px;letter-spacing:-.035em;line-height:1.04}
.h3{font-weight:700;font-size:40px;letter-spacing:-.02em;line-height:1.15}
.sub{font-weight:400;font-size:32px;color:var(--mute);line-height:1.3}
.grad{background:linear-gradient(90deg,#c9c1ff,#7b6cff 55%,#43d3ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.tile{width:120px;height:120px;border-radius:30px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 20px 50px rgba(0,0,0,.45);flex:none}
.tile img{width:76px;height:76px}
.tile.sm{width:76px;height:76px;border-radius:18px}.tile.sm img{width:48px;height:48px}
.card{background:rgba(18,19,30,.78);border:1px solid rgba(255,255,255,.09);border-radius:28px;box-shadow:0 30px 80px rgba(0,0,0,.5)}
.stat{font:800 92px var(--font-mono);letter-spacing:-.04em}
.row{display:flex;align-items:center;gap:28px}
.chip{display:inline-flex;align-items:center;gap:14px;padding:16px 28px;border-radius:999px;background:rgba(123,108,255,.14);border:1px solid rgba(179,168,255,.35);font-weight:700;font-size:34px}
.brow{display:flex;align-items:center;margin-bottom:34px}
.bar{height:82px;border-radius:14px;transform-origin:0 50%}
.blabel{width:430px;font-weight:700;font-size:38px;display:flex;align-items:center;gap:18px;flex:none}
.bval{font:800 46px var(--font-mono);margin-left:22px}
.lt{z-index:8;left:110px;bottom:96px;padding:22px 36px 22px 30px;display:flex;align-items:center;gap:24px;border-radius:22px;background:rgba(10,11,18,.82);border:1px solid rgba(255,255,255,.12)}
.lt .acc{width:8px;height:58px;border-radius:4px;background:linear-gradient(#b3a8ff,#43d3ff)}
.dot{width:14px;height:14px;border-radius:50%;background:rgba(255,255,255,.28)}
'''
JS = r'''
const tl = gsap.timeline({ paused: true });
const ST = {
  full:   {clip:"inset(0px 0px 0px 0px round 0px)", x:0, y:0, scale:1},
  split:  {clip:"inset(24px 504px 24px 504px round 28px)", x:456, y:0, scale:1},
  circle: {clip:"inset(70px 680px 450px 680px round 280px)", x:700, y:394.5, scale:0.55},
  square: {clip:"inset(30px 560px 290px 560px round 36px)", x:-460, y:0, scale:0.9}
};
const FRAME = {circle:"#ringC", split:"#frameR", square:"#frameS"};
let cur = "full";
function cam(state, t, d){
  d = d || 0.7; const s = ST[state];
  tl.to("#cam", {clipPath:s.clip, x:s.x, y:s.y, scale:s.scale, duration:d, ease:"power3.inOut"}, t);
  if (FRAME[cur]) tl.to(FRAME[cur], {opacity:0, duration:0.25}, t);
  if (FRAME[state]) tl.to(FRAME[state], {opacity:1, duration:0.35}, t + d - 0.15);
  cur = state;
}
function inn(sel, t, o){ tl.from(sel, Object.assign({opacity:0, y:40, duration:0.55, ease:"power3.out"}, o||{}), t); }
function outScene(sel, t){ tl.to(sel, {opacity:0, duration:0.35, ease:"power2.in"}, t); }
function count(id, to, t, d, dec, from){
  const o = {v: from||0};
  tl.to(o, {v:to, duration:d, ease:"power2.out", onUpdate:()=>{ document.getElementById(id).textContent = dec ? o.v.toFixed(dec) : Math.round(o.v).toLocaleString("en-US"); }}, t);
}
function bars(prefix, t){
  tl.from("."+prefix+" .brow", {opacity:0, x:-30, duration:0.45, stagger:0.18, ease:"power2.out"}, t);
  document.querySelectorAll("."+prefix+" .bar").forEach((b,i)=>{ tl.from(b, {scaleX:0, duration:0.9, ease:"power3.out"}, t + i*0.18); });
}
'''
# square frame: box 800x760 scaled .9 = 720x684, centre (500,423) -> left 140, top 81
def bars(rows, vmax, W=820):
    out=[]
    for name, icon, val, col, hi in rows:
        ic = f'<div class="tile sm"><img src="assets/icons/{icon}.svg"></div>' if icon else '<div class="tile sm" style="background:#2a2c3d"></div>'
        w = int(W*val/vmax)
        bg = f"linear-gradient(90deg,{col},{col}cc)"
        op = "1" if hi else ".55"
        out.append(f'<div class="brow">{ic and ""}<div class="blabel">{ic}<span>{name}</span></div><div class="bar" style="width:{w}px;background:{bg};opacity:{op}"></div><div class="bval" style="opacity:{op}">{val}</div></div>')
    return "".join(out)
Q="#8b7dff"; G="#7d8396"; R="#ff5d73"; GR="#3fe0a0"
deep=bars([("Qwen4-Max","qwen-color",75.7,Q,1),("Kimi K3.1","kimi-color",75.5,G,0),("GPT-6.1 Sol","openai",75.2,G,0),("Opus 5.5","claude-color",74.2,G,0)],76)
ale=bars([("Qwen4-Max","qwen-color",46.7,GR,1),("Opus 5.5","claude-color",43.4,G,0),("Kimi K3.1","kimi-color",43.4,G,0),("Qwen3.8-Max","qwen-color",27.9,G,0)],47)
tb=bars([("Kimi K3.1","kimi-color",67.2,G,0),("Qwen4-Max","qwen-color",48.5,R,1)],68)
pb=bars([("Opus 5.5","claude-color",65.0,G,0),("Qwen4-Max","qwen-color",31.5,R,1)],68)
# dots: 40x14=560 dots, ~3% lit = 17
import random
rnd=random.Random(4); lit=set(rnd.sample(range(560),17))
dots="".join(f'<div class="dot {"on" if i in lit else "off"}"></div>' for i in range(560))
t=open("intro.tpl.html",encoding="utf-8").read()
for k,v in {"__CSS__":CSS,"__JSLIB__":JS,"__DOTS__":dots,"__BARS_DEEP__":deep,"__BARS_ALE__":ale,"__BARS_TB__":tb,"__BARS_PB__":pb}.items(): t=t.replace(k,v)
open("index.html","w",encoding="utf-8").write(t)
o=open("outro.tpl.html",encoding="utf-8").read().replace("__CSS__",CSS).replace("__JSLIB__",JS)
os.makedirs("../mg_outro/assets",exist_ok=True)
open("../mg_outro/index.html","w",encoding="utf-8").write(o)
for f in ["hyperframes.json","package.json","meta.json"]: shutil.copy(f,"../mg_outro/"+f)
if not os.path.exists("../mg_outro/assets/icons"): shutil.copytree("assets/icons","../mg_outro/assets/icons")
if not os.path.exists("../mg_outro/assets/outro.mp4"): shutil.copy("assets/outro.mp4","../mg_outro/assets/outro.mp4")
print("ok")
