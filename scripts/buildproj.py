"""Build the VibezCut project (.fcproj) from pieces.json. Headless: works with the app open or closed.

  python buildproj.py <video> project.json [--workdir DIR]

project.json (everything except "out" is optional):
  {"out": "D:/.../My Video - Edit v1.fcproj",
   "name": "My Video - Edit v1",
   "gain_db": "auto",                 # "auto" = measure edit16k.wav, aim at -14 LUFS / -1 dB peak; or a number
   "inserts":  [{"file": "sponsor.mp4", "before_unit": 22}],        # whole clip cut into V1/A1 (mid-roll)
   "overlays": [{"file": "intro_mg.mp4", "at": 0},                  # V2, no audio; "at" = timeline seconds
                {"file": "outro_mg.mp4", "at_unit": 64}],           # or the start of a unit
   "audio":    [{"file": "audio/music_bed.wav", "track": "A2"}, {"file": "audio/sfx.wav", "track": "A3"}],
   "width": 1920, "height": 1080, "fps": 60}                        # fps defaults to the video's own

Relative paths are relative to the video's folder. Writes timeline_map.json in the workdir: the timeline
time of every piece and unit, for timing motion graphics, music and SFX against the cut.
"""
import argparse, json
from pathlib import Path
import _kit

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("project"); ap.add_argument("--workdir", default="")
a = ap.parse_args()
VIDEO, WD = _kit.setup(a.video, a.workdir or None)
cfg = _kit.load_json_arg(a.project)
ROOT = Path(VIDEO).parent
P = lambda p: str(p if Path(p).is_absolute() else ROOT / p)
from studio import fc  # noqa: E402
from studio.build import Builder, push_transcript  # noqa: E402

pieces = json.loads((WD / "pieces.json").read_text())
dur, vfps = _kit.probe(VIDEO)
fps = int(round(cfg.get("fps") or vfps or 60))
OUT = P(cfg["out"])
name = cfg.get("name") or Path(OUT).stem
gain = cfg.get("gain_db", "auto")
if gain == "auto":
    gain, lufs, tp = _kit.auto_gain(WD)
    print(f"voice measures {lufs} LUFS, peak {tp} dB -> gain {gain:+} dB")
inserts = {}
for ins in cfg.get("inserts", []):
    inserts.setdefault(int(ins["before_unit"]), []).append(P(ins["file"]))

c = fc.Headless()
try:
    b = Builder(c, fps)
    b.run("file.newProject", {"name": name})
    imp = lambda p: b.run("file.import", {"paths": [p]})["items"][0]
    src = imp(VIDEO)
    b.run("file.newSequence", {"name": name, "width": cfg.get("width", 1920), "height": cfg.get("height", 1080),
                               "fps": fps, "sampleRate": 48000, "video": 4, "audio": 3})
    pos = 0; vclips = []; tmap = {"fps": fps, "pieces": [], "units": {}, "inserts": []}
    done = set()
    for s, e, u in pieces:
        if u in inserts and u not in done:
            done.add(u)
            for f in inserts[u]:
                nf = int(round(_kit.probe(f)[0] * fps))
                b.run("timeline.place", {"item": imp(f), "track": "V1", "audioTrack": "A1", "time": pos * b.ft})
                tmap["inserts"].append({"file": f, "at": pos / fps, "duration": nf / fps})
                pos += nf
        tmap["units"].setdefault(str(u), pos / fps)
        nf = int(round((e - s) * fps))
        r = b.run("timeline.place", {"item": src, "track": "V1", "audioTrack": "A1", "time": pos * b.ft,
                                     "sourceIn": b.tk(s), "duration": nf * b.ft})
        vclips += r["clips"]
        tmap["pieces"].append([round(pos / fps, 3), s, e, u])
        pos += nf
    for ov in cfg.get("overlays", []):
        t = tmap["units"][str(ov["at_unit"])] if "at_unit" in ov else float(ov.get("at", 0))
        b.run("timeline.place", {"item": imp(P(ov["file"])), "track": ov.get("track", "V2"),
                                 "time": int(round(t * fps)) * b.ft, "audio": False})
    for tr, nm in {"V1": "Camera + Screen", "V2": "Motion Graphics", "A1": "Voice", "A2": "Music", "A3": "SFX"}.items():
        try:
            b.run("timeline.setTrack", {"track": tr, "name": nm})
        except Exception:
            pass
    if gain:
        b.run("clip.audioGain", {"clips": vclips, "mode": "set", "db": gain})
    for au in cfg.get("audio", []):
        b.run("timeline.place", {"item": imp(P(au["file"])), "track": au["track"], "time": 0, "video": False})
    push_transcript(b, src, VIDEO)
    b.run("file.saveAs", {"path": OUT})
    tmap["duration"] = pos / fps; tmap["gain_db"] = gain
    (WD / "timeline_map.json").write_text(json.dumps(tmap), encoding="utf-8")
    print("saved", OUT, "length", round(pos / fps, 2), "s; inserts", tmap["inserts"])
finally:
    c.close()
