"""Exact word times and quiet gaps inside source windows, for placing a cut by hand.

  python probe.py <video> "[[t0,t1],[t0,t1]]" [--workdir DIR]
"""
import argparse
import _kit
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("windows"); ap.add_argument("--workdir", default="")
a = ap.parse_args()
VIDEO, WD = _kit.setup(a.video, a.workdir or None)
from studio import audio  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

x = audio.load16(WD / "audio16k.wav"); db = np.load(WD / "db.npy")
M = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
for t0, t1 in _kit.load_json_arg(a.windows):
    segs, _ = M.transcribe(x[int(t0 * 16000):int(t1 * 16000)], word_timestamps=True, language="en",
                           condition_on_previous_text=False, vad_filter=False)
    ws = [f"{k.word.strip()}({t0 + k.start:.2f}-{t0 + k.end:.2f})" for s in segs for k in s.words]
    q = [(round(p, 2), round(r, 2)) for p, r in audio.runs(db, -50, 4) if t0 <= p <= t1]
    print(f"== {t0}-{t1}\n", " ".join(ws), "\n quiet<-50:", q)
