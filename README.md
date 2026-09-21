# 仮名決闘 — Kana Duel

A single-file browser game for learning to read hiragana and katakana.

**Play it:** https://psatkins.github.io/kana-game/

## What's here

- `index.html` — the entire game. No build step, no dependencies. Open it in a
  browser and it runs.
- `make_audio_pack.py` — optional, generates a pack of spoken-mora recordings.

## Modes

The dojo is the grid. Kana are drawn either in 五十音図 table order or
shuffled, in hiragana, katakana, or both, and a card speaks when you turn it.
Glyphs render as brush (筆), handwriting (手書き), or Mincho print (明朝), so a
kana learned in one hand doesn't become unrecognizable in another.

稽古 Drill is the same pool with the stakes taken out. Twenty characters by
multiple choice, then the same twenty typed from memory, then an account of
what you missed — no clock, no hit points, and a way out on every screen.
Turning a card only ever asks you to agree with it; this is the part that asks
you to produce the answer from nothing, which is the one thing the duel
demands. The wrong answers offered are near-misses rather than filler: the
game already knows which mora the eye and ear run together, and draws the
decoys from exactly those. Half of each draw leans on the characters you have
got wrong before, and a character leaves that list by being typed correctly
with no choices in front of it.

The duel is where it is tested. You answer by reading left-to-right, in gojūon
order, or by listening, against a ladder of opponents who do not wait.

## Audio

Sound needs no setup. The game speaks each mora with the Japanese voice already
installed on the device, and synthesises its chimes in the browser — nothing is
downloaded and no files are required.

Voice selection is deliberate rather than first-match. macOS ships novelty
voices that also report themselves as `ja-JP` — Eddy, Grandma, Rocko — and they
mangle isolated mora badly enough to make ふ and く indistinguishable, so the
game ranks explicitly and prefers Kyoko. Where no Japanese voice is installed
at all, it says so and falls back to reading the romaji aloud in English.

Human recordings still beat synthesis on exactly those confusable pairs, so the
"Load recordings…" button accepts a folder of clips named by romaji (`a.mp3`,
`ka.mp3`, `shi.mp3`, `kya.mp3` …), keeps them in the browser, and uses a clip
wherever one exists. Recordings are supplied by whoever is playing rather than
shipped with the game: their licence is theirs to honour, not the game's to
assume.

`make_audio_pack.py` generates such a pack:

```bash
export GOOGLE_TTS_KEY=...        # Google Cloud TTS key
python3 make_audio_pack.py --engine google
```

Other engines are available via `--engine`, including a local VOICEVOX server
and macOS `say`. The mora list is parsed out of `index.html`, so a pack can
never drift from what the game actually asks you to identify.
