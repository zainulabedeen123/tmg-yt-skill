"""Turn units.json into exact cut points and pieces.json. Use this instead of studio_resolve + studio_assemble.

  python cut.py <video> [--removals "[[t0,t1],...]" | removals.json] [--workdir DIR]

Reads units.json, phrases.json and db.npy from the workdir (studio_transcribe and studio_save_units put
them there). Each unit: {text, k1, k2, sw?, ew?, fixS?, fixE?}. Start and end snap to the nearest quiet
run so no word is clipped; fixS / fixE force an exact source time. Writes resolved.json and pieces.json.
"""
import argparse, json
import _kit
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--removals", default=""); ap.add_argument("--workdir", default="")
a = ap.parse_args()
VIDEO, WD = _kit.setup(a.video, a.workdir or None)
rem = _kit.load_json_arg(a.removals, [])
from studio import assemble, audio, transcribe  # noqa: E402

db = np.load(WD / "db.npy")
R = audio.runs(db, -56, 3)
ph = [(x["s"], x["e"]) for x in transcribe.phrases(VIDEO)]
units = json.loads((WD / "units.json").read_text(encoding="utf-8"))
res = {}
for i, u in enumerate(units):
    text = u["text"] if isinstance(u["text"], str) else u["text"][0]
    s1 = ph[u["k1"]][0]; e2 = ph[u["k2"]][1]
    if u.get("fixS"):
        S = u["fixS"]
    elif u.get("sw"):
        a0, a1 = u["sw"]
        c = [(x, y) for x, y in R if a0 - 0.3 <= y <= a1 + 0.04]
        if c:
            x, y = max(c, key=lambda r: r[1]); S = (x + y) / 2 if y - x < 0.12 else y - 0.07
        else:
            S = a0 - 0.02
    else:
        c = [(x, y) for x, y in R if s1 - 0.6 <= y <= s1 + 0.05]
        if c:
            x, y = max(c, key=lambda r: r[1]); S = (x + y) / 2 if y - x < 0.14 else y - 0.08
        else:
            S = s1 - 0.06
    if u.get("fixE"):
        E = u["fixE"]
    else:
        w0, w1 = u["ew"] if u.get("ew") else (e2 - 0.06, e2 + 0.5)
        c = [(x, y) for x, y in R if w0 <= x <= w1]
        if c:
            x, y = min(c, key=lambda r: r[0]); E = (x + y) / 2 if y - x < 0.16 else x + 0.12
        else:
            E = w1 if u.get("ew") else e2 + 0.12
    res[str(i)] = {"S": round(S, 3), "E": round(E, 3), "ok": True, "t": text, "i": i}
(WD / "resolved.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(assemble.build_pieces(VIDEO, rem))
# build_pieces does not apply a removal across a piece boundary: drop pieces that sit inside one
pp = json.loads((WD / "pieces.json").read_text())
pp = [p for p in pp if not any(x - 0.15 <= p[0] and p[1] <= y + 0.15 for x, y in rem)]
(WD / "pieces.json").write_text(json.dumps(pp))
print("pieces", len(pp), "length", round(sum(e - s for s, e, _ in pp), 2), "s ->", WD / "pieces.json")
