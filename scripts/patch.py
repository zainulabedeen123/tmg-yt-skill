"""Apply fixes to units.json by matching the start of a unit's text.

  python patch.py <video> patches.json [--workdir DIR]

patches.json:
  [{"match": "and 2.4 trillion", "fixS": 163.64},
   {"match": "Fable 5.2.", "fixS": 712.08, "fixE": 712.70},
   {"match": "That looks natural", "replace": [{"text": "...", "k1": 778, "k2": 778, "fixS": 1703.10, "fixE": 1704.12}]},
   {"match": "um so anyway", "drop": true}]
"""
import argparse, json
import _kit

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("patches"); ap.add_argument("--workdir", default="")
a = ap.parse_args()
VIDEO, WD = _kit.setup(a.video, a.workdir or None)
p = WD / "units.json"
U = json.loads(p.read_text(encoding="utf-8"))
for pt in _kit.load_json_arg(a.patches):
    hit = [i for i, u in enumerate(U)
           if (u["text"] if isinstance(u["text"], str) else u["text"][0]).startswith(pt["match"])]
    if len(hit) != 1:
        raise SystemExit(f'"{pt["match"]}" matches {len(hit)} units, need exactly 1')
    i = hit[0]
    if pt.get("drop"):
        U[i:i + 1] = []
    elif "replace" in pt:
        U[i:i + 1] = pt["replace"]
    else:
        U[i].update({k: v for k, v in pt.items() if k != "match"})
p.write_text(json.dumps(U, indent=1), encoding="utf-8")
print("patched", p, "units", len(U))
