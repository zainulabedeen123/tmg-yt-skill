---
name: tmg-yt-edit
description: TMG YT Edit - the fast pipeline for editing a long-form YouTube video from raw footage. Precise cut of silences, bad takes and repeats into a VibezCut project, then motion graphics, sponsor, music, SFX, captions, render, thumbnail, metadata and a Short. Use when the user says /tmg-yt-edit, "TMG edit", "edit my next video", gives raw footage to cut, or asks for a stage of this pipeline ("stage 2", "add the motion graphics", "stage 4", "make the Short").
---

# TMG YT Edit: long-form YouTube edit in four stages

The user is not technical. Write plainly, put deliverables (descriptions, lists) straight in chat, no fluff.
Do the stage that was asked for and stop; do not start the next stage on your own.

## How the user starts a stage
The user types `/tmg-yt-edit stage N` followed by a few filled-in fields (the forms are in `PROMPTS.md`; if they
ask for the prompts, print that file's short forms in chat). Stage 1 = cut, 2 = graphics / sound / captions /
render, 3 = thumbnail and metadata, 4 = the Short. With no stage given, ask which one and show the form for it.
If a needed field is empty, ask for all missing fields in one message.

## Updating
This folder is a git checkout of `github.com/zainulabedeen123/tmg-yt-skill` (private, shared with the channel's editors. It holds a licensed music track, so it must stay private: if it is ever made public, remove `assets/music/*.wav` from the repo and its history first). When the user says "update
yourself" or "update the skill": `git -C KIT pull`, then say what changed (`git log -3 --oneline`). When the owner
asks to change the skill, edit the files here, commit and `git push` so the editors get it.

## First run on a PC
Run `python KIT/scripts/check.py` (any Python 3; `py -3` also works). It prints OK / NEED lines and READY or
NOT READY, and writes `KIT/python.txt`. Fix every NEED line for the user (`check.py --install` adds the Python
packages; `winget install ffmpeg`; VibezCut itself must be installed by the user). Do this once, and again
whenever a script fails to start.

Paths used below:
- `KIT` = this skill's folder. Scripts in `KIT/scripts`, templates in `KIT/templates`, icons / SFX / music in `KIT/assets`.
- `PY` = the Python path stored in `KIT/python.txt` (it has numpy and faster-whisper). No file yet = run the check.
- VibezCut lives in `%LOCALAPPDATA%/VibezCut/current/` (studio package and `vibezcut-cli.exe`).
- Every script takes the raw video path first and works in `<video folder>/_studio/<video name>/` (the workdir).
  Run them from `KIT/scripts` (`cd` there first). Each has usage notes at the top of the file.

## Speed rules (these are why the kit exists)
- NEVER call `studio_resolve` or `studio_assemble`: they stalled for 30+ minutes. `cut.py` does both in under a second.
- Before transcribing, check free memory. If Slack or another app is holding many GB, ask the user to close it.
- One check pass per cut (`verify.py`), fix what it lists, run it once more to confirm, then stop. Anything still
  doubtful goes to the user as a list with timestamps. Do not loop.
- Ask for everything missing in ONE message before starting, not along the way.
- Renders that take over ~2 minutes run in the background.

## Stage 1: the cut

Inputs: folder, file, names to spell right, script (optional).

1. `studio_transcribe(video, terms="<product names>")`. Read ALL of `studio_read_transcript` before choosing.
2. Choose units `{text, k1, k2, sw?, ew?}` and `studio_save_units`. Rules:
   - Remove silences, bad takes, false starts, stutters, repeated words and points, recording chatter.
   - Default to the LAST complete take of a sentence; take an earlier one only when the last has a clear flaw.
   - When the user says "cut" out loud, the take before it is bad (drop the word "cut" too).
   - The script only shows intent and order. Keep good unscripted lines.
   - A repeat hidden inside one phrase: set `sw` to the window of the last repeat (`studio_words` shows word times).
3. `PY cut.py "<video>"` -> `pieces.json`. Add `--removals "[[t0,t1],...]"` to cut source ranges out.
4. `PY verify.py "<video>"` -> edited transcript + ISSUES (REP / PAIR), and `edit16k.wav`.
   Fix with `PY probe.py "<video>" "[[t0,t1]]"` (exact word times and quiet gaps), then
   `PY patch.py "<video>" patches.json` (fixS / fixE / replace / drop by text match) or removals. Re-run cut + verify once.
   Cuts go in the quiet gap between words: no clipped word endings, no hiss fragment at a sentence edge.
5. `PY buildproj.py "<video>" project.json` with `{"out": "<folder>/<Title> - Edit v1.fcproj"}`. Voice gain is
   "auto": it measures the edit and raises the voice as far as the peaks allow (peak at -1 dB). Never a fixed
   number. The final -14 LUFS is set at export by `loudness.py` (stage 2, step 8).
6. `fc_open(path)`. If VibezCut is not running, say so and give the path to open.
7. Report: final length, and the doubtful spots with timestamps. No graphics, music or captions in this stage.

## Stage 2: graphics, sound, captions, render

Inputs: changes to the cut, sponsor type, opening montage moments, music, notes file.
Sponsor type is one of:
- **none**: skip everything about sponsors.
- **mid-roll**: a sponsor clip cut into the video. Use `templates/sponsor/timer.tpl.html` (countdown "back to the
  video in m:ss"), render it, and put it in `project.json` as `"inserts": [{"file": ..., "before_unit": N}]`.
  Music is muted over it (`"mute"` in sound.json).
- **whole video sponsored**: no countdown, no insert. The sponsor's real logo and name appear in the graphics
  where the user talks about it, and the sponsor link goes first in the description.

Steps:
1. Apply any cut changes (stage 1 tools), rebuild. `timeline_map.json` in the workdir then gives the timeline time
   of every unit: time all graphics, music and SFX from it.
2. Find the talking-head parts (transcript + a few `fc_frame` checks). Graphics go ONLY there, never over screen share.
3. **Scene list first.** Show the user the look in one line (colours, type, feel), then a short table: time, layout,
   what is on screen. Wait for the OK. Rendering is
   the expensive part; a line of text is cheap to change.
4. Build with HyperFrames (read the `hyperframes` skill for the contract).
   **Design a new look for every video.** Do NOT reuse the Qwen 4 Max look (violet / cyan on dark grid, its cards,
   bars and type) or any earlier video's look: the user said so. Choose palette, type, shapes and motion from this
   video's topic and the brands in it, and state the look in one line of the scene list so the user approves it.
   What IS reusable is the mechanics only: `templates/mg/mgkit.py` has the camera states (full / split / circle /
   square) and timeline helpers; write fresh CSS for the look. `templates/mg/examples/` shows how a finished scene
   is wired, as a technical reference, never as a design to copy. Real product logos: `KIT/assets/icons` first,
   otherwise fetch the official SVG. Numbers and names must match what is said.
   Opening (first 6-7 s and the intro after it): fast-paced and attention-grabbing. Quick cuts, energetic
   animation, something new on screen about every second. Start with a montage of the video's best demo moments;
   with no demos, open on the boldest claim or number as big animated text. High-energy music from frame one,
   louder than the rest of the video (about 10-12 dB under the voice, voice still clearly on top), dropping to the
   normal 18 dB under once the intro ends: build it as its own section of the bed, since audio.py only has "lower"
   and "mute" ranges (set under_db for the opening level and "lower" the rest). SFX on every cut and every graphic
   that lands: whoosh, impact, pop, a riser into the title.
   The `/effects` skill is for vertical face video: use it in the Short, not here.
5. Sound: `PY audio.py "<video>" sound.json` -> `audio/music_bed.wav` + `audio/sfx.wav` (music 18 dB under the voice,
   lower under screen share, subtle SFX on layout changes). Default music is `KIT/assets/music/default_bed.wav` (licensed for this channel's videos only; never send the file anywhere else).
6. Rebuild the project with overlays and audio in `project.json`.
7. Captions last: `studio_captions` on the open project. Default: karaoke box in lime (#c6f432), current word
   highlighted, drop shadow, clear of graphics and face. Pass product-name `corrections`.
8. Draft: export "Quick Preview 720p (fast draft)". After approval, one final export:
   `vibezcut-cli.exe --project X export out.mp4 --preset "YouTube 1080p Full HD"`
   (CLI in `%LOCALAPPDATA%/VibezCut/current/`).
9. ALWAYS finish with `PY loudness.py "<export>.mp4" "<Title> - Final.mp4"`: it brings the audio to -14 LUFS
   (YouTube's level) without touching the picture, and prints before / after. The Qwen 4 Max final went out at
   -27 LUFS because this step did not exist. Tell the user nobody has listened to it: they play it before upload.

## Stage 3: thumbnail and metadata (after the final render is approved)

1. Thumbnail: Keyframe connector `thumbnail_design`, model `openai/gpt-image-2.5-sunburst`, 2 options, 16:9:
   the presenter's face, the product's real logo, 2-4 big words that create curiosity.
2. Title options (3), description, chapters (from `timeline_map.json`, starting 0:00), tags, 3-10 hashtags: all
   written in chat. The sponsor link is included exactly as given.

## Stage 4: the Short (separate vertical video, under 60 s, 1080x1920)

- Strongest 6-8 sentences: a complete story with a hook and a punchline.
- `/effects` (orbit, noise, lineup, ...) on the moments where they fit.
- Face always on screen: full face, half split with the background removed so the head pops over the top panel,
  or a small box.
- Safe areas (this rule is for the Short only): keep the top 220 px, bottom 420 px and right 140 px clear.
- Bold word-by-word captions, spoken word highlighted; music well under the voice; SFX on layout changes; final
  loudnorm to -14 LUFS.
- `templates/short/` shows the layout mechanics (safe areas, cut-out head, captions); design a new look per Short.
- Say plainly what was not checked.

## What is tested (16 Nov 2026, against the Qwen 4 Max project)
- `cut.py`: same pieces.json as the delivered cut, byte for byte, in 0.5 s.
- `verify.py`: same issue list as the original check.
- `buildproj.py`: same 801.6 s timeline, sponsor insert at 144.35 s, 24 s to build.
- `templates/mg/mgkit.py`: rebuilds the Qwen intro composition byte for byte.
- `audio.py`: runs; music measured 16-17 dB under the gained voice, silent in the muted range.
- `loudness.py`: -27.5 -> -14.3 LUFS on a 90 s excerpt, peak -1.4 dB.
- Not tested: `patch.py` and `probe.py` after the rewrite (logic unchanged, arguments new), and the default
  workdir path (tests used `--workdir`). The sponsor timer template is the Qwen one with the length as `__DUR__`.
