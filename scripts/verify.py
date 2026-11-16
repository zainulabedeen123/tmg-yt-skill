"""Check the cut: render the edited dialogue (edit16k.wav), transcribe it again, flag repeats.

  python verify.py <video> [--workdir DIR] [--model small.en]

Prints the edited transcript with source times, then ISSUES: REP (same word twice) and PAIR (two words
repeated). Also saved as verify.txt. Run it once per cut; fix what it lists with fixS / fixE / removals.
"""
import argparse, json, re, wave
import _kit
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--workdir", default=""); ap.add_argument("--model", default="small.en")
a = ap.parse_args()
VIDEO, WD = _kit.setup(a.video, a.workdir or None)
from studio import audio, transcribe  # noqa: E402

x = audio.load16(WD / "audio16k.wav")
P = json.loads((WD / "pieces.json").read_text())
out = []; mp = []; t = 0
for s, e, i in P:
    seg = x[int(s * 16000):int(e * 16000)].copy(); n = len(seg); f = min(200, n // 2)
    seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
    out.append(seg); mp.append((t, s, i)); t += n / 16000
y = np.concatenate(out).astype(np.float32)
w = wave.open(str(WD / "edit16k.wav"), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
from faster_whisper import WhisperModel  # noqa: E402
M = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=8)
segs, _ = M.transcribe(y, word_timestamps=True, vad_filter=False, condition_on_previous_text=False,
                       beam_size=5, temperature=0, initial_prompt=transcribe.VERBATIM)


def src(tt):
    best = mp[0]
    for m in mp:
        if m[0] <= tt: best = m
    return round(best[1] + tt - best[0], 2), best[2]


lines = []; words = []
for s in segs:
    lines.append(f"{s.start:7.1f} src{src(s.start)}  {s.text.strip()}")
    words += [(re.sub(r"[^a-z0-9']", "", k.word.lower()), k.start) for k in s.words]
words = [k for k in words if k[0]]
iss = []
for i in range(len(words) - 1):
    if words[i][0] == words[i + 1][0] and words[i][0] not in {"really", "very", "bye"} and not words[i][0].isdigit():
        iss.append(f"{words[i][1]:7.1f} src{src(words[i][1])} REP: " + " ".join(k[0] for k in words[max(0, i - 4):i + 6]))
for i in range(len(words) - 3):
    if words[i][0] == words[i + 2][0] and words[i + 1][0] == words[i + 3][0]:
        iss.append(f"{words[i][1]:7.1f} src{src(words[i][1])} PAIR: " + " ".join(k[0] for k in words[max(0, i - 3):i + 7]))
(WD / "verify.txt").write_text("\n".join(lines) + "\n\nISSUES\n" + "\n".join(iss), encoding="utf-8")
print("\n".join(lines)); print("ISSUES"); print("\n".join(iss))
print("edit length", round(t, 1), "s; issues", len(iss), "->", WD / "verify.txt")
