"""Shared helpers for the yt-edit kit. Every script takes the raw video path as its first argument."""
import json, os, re, subprocess, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
STUDIO = os.environ.get("VIBEZCUT_STUDIO", str(Path.home() / "AppData/Local/VibezCut/current/studio"))
sys.path.insert(0, STUDIO)
from studio import config  # noqa: E402


def setup(video, workdir=None):
    """Returns (video, workdir). Default workdir is the studio one: <video dir>/_studio/<stem>/."""
    video = str(Path(video).resolve())
    if workdir:
        wd = Path(workdir).resolve()
        wd.mkdir(parents=True, exist_ok=True)
        config.workdir = lambda v: wd
    else:
        wd = config.workdir(video)
    return video, wd


def load_json_arg(s, default=None):
    """A JSON string, or a path to a JSON file."""
    if not s:
        return default
    if s.lower().endswith(".json") and Path(s).exists():
        return json.loads(Path(s).read_text(encoding="utf-8"))
    return json.loads(s)


def probe(path):
    """(duration seconds, fps or None) of a media file."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    fps = None
    for s in j.get("streams", []):
        if s.get("codec_type") == "video":
            a, b = s["r_frame_rate"].split("/")
            fps = float(a) / float(b)
            break
    return float(j["format"]["duration"]), fps


def auto_gain(wd, target_lufs=-14.0, peak_db=-1.0):
    """(gain dB, measured LUFS, measured true peak) for the voice so the edit lands near target_lufs
    without peaks above peak_db. Needs edit16k.wav (written by verify.py)."""
    f = Path(wd) / "edit16k.wav"
    if not f.exists():
        raise SystemExit("run verify.py first: it writes edit16k.wav, which the gain is measured from")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af",
                        "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    j = json.loads(m.group(0))
    i, tp = float(j["input_i"]), float(j["input_tp"])
    return round(min(target_lufs - i, peak_db - tp), 1), i, tp
