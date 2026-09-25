# 仮名夜行 — Kana Night Parade

A single-file browser game for learning to read hiragana and katakana.
Something is standing in the road; you read its name aloud and it lets you
pass.

**Play it:** https://psatkins.github.io/kana-game/

There is a second game in here for a different reader:
[変体仮名歌留多](https://psatkins.github.io/kana-game/hentaigana.html), a karuta
match played with hentaigana, for people who already read modern kana and want
the 285 historical forms.

## What's here

- `index.html` — the whole kana game. No build step, no dependencies. Open it
  in a browser and it runs.
- `hentaigana.html` — the hentaigana karuta game, on the same terms.
- `audio/` — where a pack of spoken-mora recordings goes, if you have one.
- `make_audio_pack.py` — optional, generates such a pack.

## Modes

The dojo is the grid. Kana are drawn either in 五十音図 table order or
shuffled, in hiragana, katakana, or both, and a card speaks when you turn it.
Glyphs render as brush (筆), handwriting (手書き), or Mincho print (明朝), so a
kana learned in one hand doesn't become unrecognizable in another. Every kanji
in the interface carries furigana, because the people using this cannot read
kanji yet — which makes the chrome itself practice rather than an obstacle.

The basic set is the 46 kana a first-year course teaches. ゐ and ゑ are in the
game but not in that set: they have not been in ordinary use since 1946, and
they sit in their own row for anyone reading premodern text.

稽古 Drill is the same pool with the stakes taken out. Twenty characters by
multiple choice, then the same twenty typed from memory, then an account of
what you missed — no clock, no hit points, and a way out on every screen.
Turning a card only ever asks you to agree with it; this is the part that asks
you to produce the answer from nothing, which is the one thing the road
demands. The wrong answers offered are near-misses rather than filler: the
game already knows which mora the eye and ear run together, and draws the
decoys from exactly those. Half of each draw leans on the characters you have
got wrong before, and a character leaves that list by being typed correctly
with no choices in front of it.

The night road is where it is tested. Six encounters — 一つ目小僧, 天狗, 鎌鼬,
のっぺらぼう, 分福茶釜, 百鬼夜行 — and naming a thing is how you get past it, so
the student's verb and the character's verb are the same. You name what comes
at you by typing its romaji; then you seal it by picking, out of three paper
charms, the one whose mora you just heard. Characters are read right to left,
the way Japanese is.

Nothing is timed in the dojo, nothing is lost in the drill, and 帰る Leave sits
beside the input on every screen of the road.

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
wherever one exists.

That is per-browser, which is fine for one person and useless for a class. A
pack can also ship with the game instead, so nobody has to load anything: drop
the clips in `audio/`, list their romaji in `audio/pack.json`, and everyone at
the URL hears them. Leave that list empty — as it is now — and the game uses the
device's own Japanese voice exactly as before. A pack a player loads themselves
still takes precedence over the shipped one.

No recordings are included here. Whose voice it is, and under what terms, is for
whoever records it to decide: their licence is theirs to honour, not the game's
to assume.

`make_audio_pack.py` generates such a pack:

```bash
export GOOGLE_TTS_KEY=...        # Google Cloud TTS key
python3 make_audio_pack.py --engine google
```

Other engines are available via `--engine`, including a local VOICEVOX server
and macOS `say`. The mora list is parsed out of `index.html`, so a pack can
never drift from what the game actually asks you to identify.
