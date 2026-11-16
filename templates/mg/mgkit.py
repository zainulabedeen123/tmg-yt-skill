"""Mechanics for 16:9 motion graphics over a talking head (HyperFrames + GSAP).

The CSS below is the look of ONE video (Qwen 4 Max). Do not reuse that look: every video gets a new design.
Reuse only the camera states and helpers in JS; pass your own CSS to render(..., css=...).

Use from a per-video build script:

    import sys; sys.path.insert(0, r"<kit>/templates/mg")
    import mgkit
    html = open("scene.tpl.html", encoding="utf-8").read()      # contains __CSS__ and __JSLIB__
    mgkit.render(html, "index.html", {"__BARS__": mgkit.bars([...], vmax=76)})

examples/intro.tpl.html and examples/outro.tpl.html are complete scenes in this style (the Qwen 4 Max
video); examples/qwen_build.py is the build script that filled them. They show the wiring, not a design to copy.

Camera states (the speaker video sits in #cam; cam("state", t) moves it):
  full    whole frame
  split   speaker on the right half, graphics on the left      (frame #frameR)
  circle  small circle bottom right, graphics full page         (ring  #ringC, at 1503,673 314px)
  square  square on the left, graphics on the right             (frame #frameS, at 140,81 720x684)
JS helpers: inn(sel, t, opts) fade/slide in, outScene(sel, t), count(id, to, t, dur, decimals, from),
bars(prefix, t). Register the timeline at the end: window.__timelines["main"] = tl; tl.seek(0);
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ICONS = HERE.parent.parent / "assets" / "icons"

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

# bar colours: highlight, neutral, losing, winning
Q = "#8b7dff"; G = "#7d8396"; R = "#ff5d73"; GR = "#3fe0a0"


def bars(rows, vmax, W=820):
    """Horizontal bar chart rows. rows: (name, icon name in assets/icons or "", value, colour, highlight)."""
    out = []
    for name, icon, val, col, hi in rows:
        ic = (f'<div class="tile sm"><img src="assets/icons/{icon}.svg"></div>' if icon
              else '<div class="tile sm" style="background:#2a2c3d"></div>')
        w = int(W * val / vmax)
        op = "1" if hi else ".55"
        out.append(f'<div class="brow"><div class="blabel">{ic}<span>{name}</span></div>'
                   f'<div class="bar" style="width:{w}px;background:linear-gradient(90deg,{col},{col}cc);opacity:{op}"></div>'
                   f'<div class="bval" style="opacity:{op}">{val}</div></div>')
    return "".join(out)


def render(tpl_html, out_path, extra=None, css=None):
    """Fill __CSS__ (your own css for this video; the Qwen CSS only if none is given), __JSLIB__ and any extra
    placeholders; write the composition."""
    t = tpl_html.replace("__CSS__", css or CSS).replace("__JSLIB__", JS)
    for k, v in (extra or {}).items():
        t = t.replace(k, v)
    Path(out_path).write_text(t, encoding="utf-8")
    return out_path
