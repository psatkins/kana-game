# 仮名決闘 — Kana Duel

A single-file browser game for learning to read hiragana and katakana.

**Play it:** https://psatkins.github.io/kana-game/

## What's here

- `index.html` — the entire game. No build step, no dependencies. Open it in a
  browser and it runs.
- `make_audio_pack.py` — generates the optional spoken-mora audio pack.

## Modes

Kana are drawn either in 五十音図 table order or shuffled, in hiragana,
katakana, or both. You answer by reading left-to-right, in gojūon order, or by
listening. Glyphs render as brush (筆), handwriting (手書き), or Mincho print
(明朝), so a kana you learned in one hand doesn't become unrecognizable in
another.

## Audio

The game ships silent. The "Load recordings…" button reads a folder of clips
named by romaji (`a.mp3`, `ka.mp3`, `shi.mp3`, `kya.mp3` …), which
`make_audio_pack.py` produces:

```bash
export GOOGLE_TTS_KEY=...        # Google Cloud TTS key
python3 make_audio_pack.py --engine google
```

Other engines are available via `--engine` (including a local VOICEVOX server,
and macOS `say`). The mora list is parsed out of `index.html`, so the pack can
never drift from what the game actually asks you to identify.

Audio is pre-generated rather than synthesised live because the page makes no
outbound network requests: no API key sits in the browser, playback is instant
and offline, and it works when published as a static file.
