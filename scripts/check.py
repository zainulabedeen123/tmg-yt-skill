"""First-run check for the TMG YT Edit kit. Runs on any Python 3 (standard library only).

  python check.py            # check; writes ../python.txt with the Python the other scripts must use
  python check.py --install  # also pip-install numpy and faster-whisper when no Python has them

Prints one line per requirement (OK / NEED), then READY or NOT READY.
"""
import os, shutil, subprocess, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
HOME = Path.home()
VC = Path(os.environ.get("LOCALAPPDATA", str(HOME / "AppData/Local"))) / "VibezCut" / "current"
NEED = "import numpy, faster_whisper"
ok = True


def say(good, name, detail=""):
    global ok
    ok = ok and good
    print(("OK    " if good else "NEED  ") + name + (": " + detail if detail else ""))


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except Exception:
        return None


def works(p, code):
    r = run([p, "-c", code])
    return bool(r and r.returncode == 0)


def pythons():
    cands = [sys.executable, shutil.which("python"), shutil.which("python3")]
    for flag in ("-3.12", "-3.11", "-3.13", "-3"):
        r = run(["py", flag, "-c", "import sys; print(sys.executable)"])
        if r and r.returncode == 0:
            cands.append(r.stdout.strip())
    cands += [str(p) for p in (HOME / "AppData/Local/Programs/Python").glob("Python3*/python.exe")]
    seen = []
    for c in cands:
        if c and Path(c).exists() and "WindowsApps" not in c and c not in seen:
            seen.append(c)
    return seen


ps = pythons()
good = next((p for p in ps if works(p, NEED)), None)
if not good and "--install" in sys.argv and ps:
    print("installing numpy and faster-whisper into", ps[0])
    subprocess.run([ps[0], "-m", "pip", "install", "numpy", "faster-whisper"])
    good = ps[0] if works(ps[0], NEED) else None
if good:
    (KIT / "python.txt").write_text(good, encoding="utf-8")
say(bool(good), "Python with numpy + faster-whisper",
    good or "none found. Install Python 3.12 (winget install Python.Python.3.12), then: python check.py --install")
say(bool(shutil.which("ffmpeg") and shutil.which("ffprobe")), "ffmpeg and ffprobe",
    "" if shutil.which("ffmpeg") else "install with: winget install ffmpeg")
say((VC / "studio" / "studio").exists(), "VibezCut studio package", str(VC / "studio"))
say(any((VC / n).exists() for n in ("vibezcut-cli.exe", "filmcraft-cli.exe")), "VibezCut command-line exporter", str(VC))
if good:
    code = "import sys; sys.path.insert(0, r'%s'); from studio import config, audio, assemble, fc, build" % (VC / "studio")
    say(works(good, code), "studio package loads in that Python")
# optional pieces: reported, but they do not block stage 1
for name, path in [("effects skill (needed for Shorts)", HOME / ".claude/skills/effects"),
                   ("hyperframes skill (needed for motion graphics)", HOME / ".claude/skills/hyperframes")]:
    print(("OK    " if path.exists() else "MISSING (optional)  ") + name)
print(("OK    " if shutil.which("npx") else "MISSING (optional)  ") + "Node.js / npx (needed for motion graphics renders)")
print("READY" if ok else "NOT READY")
