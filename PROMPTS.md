# TMG YT Edit: how to use

## Install (once per PC)

You need Git, Claude Code and VibezCut installed.

1. Open a terminal and run:

```bash
git clone https://github.com/zainulabedeen123/tmg-yt-skill.git "%USERPROFILE%/.claude/skills/tmg-yt-edit"
```

   (In PowerShell use `$env:USERPROFILE` instead of `%USERPROFILE%`.)
2. Restart Claude Code.
3. Send this once: `/tmg-yt-edit check my setup`. Claude checks Python, ffmpeg and VibezCut and installs
   what it can.

For motion graphics and Shorts you also need the `hyperframes` and `effects` skills.

Music is not included (it is licensed per person). Put your own licensed track at
`assets/music/default_bed.wav` inside the skill folder, or give a music file in the stage 2 prompt.

## Update (whenever the skill changes)

Send `/tmg-yt-edit update yourself`, or run:

```bash
git -C "%USERPROFILE%/.claude/skills/tmg-yt-edit" pull
```

## While recording

When you flub a line: pause 2 seconds, say "cut", then redo the whole sentence.

## Stage 1: the cut

```text
/tmg-yt-edit stage 1

Folder:
File:
Names to spell correctly (products, people):
Script (optional):

```

## Stage 2: motion graphics, sound, captions, render

```text
/tmg-yt-edit stage 2

Changes to the cut (if any):
Motion graphics look (optional: colours, mood, a reference; blank = a new design for this video):
Sponsor: none / mid-roll / whole video sponsored
  Mid-roll only -> file:            place it:
  Sponsor link:
Opening montage moments (timestamps, or "pick them yourself"):
Music: default track, or file:
Notes file with facts and numbers (optional):
```

## Stage 3: thumbnail and metadata

```text
/tmg-yt-edit stage 3

Thumbnail idea:
Sponsor link (if any):
```

## Stage 4: the Short

```text
/tmg-yt-edit stage 4

Angle or moment to focus on (optional):
```
