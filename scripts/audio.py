"""Make the music bed and the SFX track for the cut, as two WAV files the project places on A2 / A3.

  python audio.py <video> sound.json [--workdir DIR]

sound.json (all optional except "duration" when timeline_map.json does not exist yet):
  {"duration": 801.6,                       # timeline length; default: from timeline_map.json
   "music": "D:/.../track.wav",             # default: the kit's assets/music/default_bed.wav
   "under_db": 18,                          # music level under the (gained) voice
   "voice_gain_db": "auto",                 # the gain buildproj.py puts on the voice
   "mute":  [[144.35, 281.05]],             # no music here (a sponsor read that has its own)
   "lower": [[283.0, 767.3, 3]],            # music this many dB lower here (screen-share sections)
   "sfx":   [[0.0, "whoosh-cinematic", -6], [30.6, "pop", -14]],   # timeline s, name, dB
   "out_dir": "audio"}                      # relative to the video's folder

SFX names: files in the kit's assets/sfx (whoosh, whoosh-short, whoosh-cinematic, pop, click, click-soft,
impact-bass-1, impact-bass-2, riser, sparkle, chime, ping, notification, glitch-1..3, typing, key-press).
Risers and whooshes are placed so they lead into the given time.
"""
import argparse, json, subprocess, wave
from pathlib import Path
import _kit
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("sound"); ap.add_argument("--workdir", default="")
a = ap.parse_args()
VIDEO, WD = _kit.setup(a.video, a.workdir or None)
cfg = _kit.load_json_arg(a.sound)
ROOT = Path(VIDEO).parent
SR = 48000
SFXD = _kit.KIT / "assets" / "sfx"
tm = WD / "timeline_map.json"
T = cfg.get("duration") or json.loads(tm.read_text())["duration"]
MUS = cfg.get("music") or str(_kit.KIT / "assets" / "music" / "default_bed.wav")
if not Path(MUS).exists():
    raise SystemExit(f"no music file at {MUS}: set \"music\" in sound.json, or put your own licensed track at "
                     "assets/music/default_bed.wav in the skill folder")
OUTD = ROOT / cfg.get("out_dir", "audio"); OUTD.mkdir(parents=True, exist_ok=True)


def load(p):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(r, dtype=np.float32).reshape(-1, 2).copy()


def db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)


def save(p, x):
    w = wave.open(str(p), "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


vg = cfg.get("voice_gain_db", "auto")
if vg == "auto":
    vg = _kit.auto_gain(WD)[0]
v = load(WD / "edit16k.wav"); vdb = db(v)   # plain RMS of the edit (pauses are already cut out)
m = load(MUS); mdb = db(m)
N = int(T * SR); n = len(m); xf = int(1.5 * SR)
out = np.zeros((N, 2), np.float32); pos = 0
while pos < N:                                   # loop the track with 1.5 s crossfades
    seg = m.copy()
    if pos > 0:
        seg[:xf] *= np.linspace(0, 1, xf)[:, None]
        out[pos - xf:pos] *= np.linspace(1, 0, xf)[:, None]
        start = pos - xf
    else:
        start = 0
    end = min(N, start + n); out[start:end] += seg[:end - start]; pos = start + n
g = 10 ** ((vdb + vg - cfg.get("under_db", 18) - mdb) / 20)
env = np.full(N, g, np.float32)


def ramp(t0, t1, x, y):
    i0, i1 = max(0, int(t0 * SR)), min(N, int(t1 * SR))
    if i1 > i0: env[i0:i1] = np.linspace(x, y, i1 - i0)


for t0, t1, d in cfg.get("lower", []):
    gl = g * 10 ** (-d / 20)
    env[int(t0 * SR):int(t1 * SR)] = gl; ramp(t0 - 1.5, t0, g, gl); ramp(t1, t1 + 1.5, gl, g)
for t0, t1 in cfg.get("mute", []):
    env[int(t0 * SR):int(t1 * SR)] = 0
    ramp(t0 - 1.2, t0, float(env[max(0, int((t0 - 1.2) * SR))]), 0)
    ramp(t1, t1 + 2.0, 0, float(env[min(N - 1, int((t1 + 2.0) * SR))]))
ramp(0, 0.4, 0, float(env[min(N - 1, int(0.4 * SR))])); ramp(T - 3, T, float(env[max(0, int((T - 3) * SR))]), 0)
save(OUTD / "music_bed.wav", out * env[:, None])

sfx = np.zeros((N, 2), np.float32); cache = {}
LEAD = {"riser": 0.9, "whoosh-cinematic": 0.35, "whoosh": 0.2, "whoosh-short": 0.1}
for t, nm, gd in cfg.get("sfx", []):
    if nm not in cache:
        x = load(SFXD / (nm + ".mp3")); cache[nm] = x / (np.abs(x).max() + 1e-9)
    x = cache[nm] * 10 ** ((gd - 8) / 20)
    i = max(0, int((t - LEAD.get(nm, 0)) * SR)); j = min(N, i + len(x)); sfx[i:j] += x[:j - i]
save(OUTD / "sfx.wav", sfx)
print("voice", round(vdb, 1), "dB +", vg, "| music gain", round(20 * np.log10(g), 1), "dB | sfx events",
      len(cfg.get("sfx", [])), "->", OUTD)
