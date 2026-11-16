"""Bring a finished video to YouTube loudness. The picture is copied untouched; only the audio is redone.

  python loudness.py <in.mp4> <out.mp4> [--lufs -14] [--peak -1.5]
  python loudness.py <in.mp4>                    # measure only

Run it on every final export. Prints the loudness before and after.
"""
import argparse, json, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out", nargs="?")
ap.add_argument("--lufs", type=float, default=-14.0); ap.add_argument("--peak", type=float, default=-1.5)
a = ap.parse_args()


def measure(path, flt):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", flt + ":print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))


base = f"loudnorm=I={a.lufs}:TP={a.peak}:LRA=11"
m = measure(a.src, base)
print(f"before: {m['input_i']} LUFS, peak {m['input_tp']} dB")
if a.out:
    flt = (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
           f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-v", "error", "-i", a.src, "-c:v", "copy", "-af", flt,
                    "-ar", "48000", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", a.out], check=True)
    m2 = measure(a.out, base)
    print(f"after:  {m2['input_i']} LUFS, peak {m2['input_tp']} dB -> {a.out}")
