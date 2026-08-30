#!/usr/bin/env python3
"""
Generate an audio pack for Kana Duel.

Produces one short clip per mora, named with its romaji (a.mp3, ka.mp3,
shi.mp3, kya.mp3 ...) -- exactly what the game's "Load recordings..." button
expects. The mora list is read out of index.html, so it can never drift from
what the game actually asks you to identify.

Why pre-generate instead of calling a TTS API from the page:
  - A published Artifact blocks outbound network requests, so a live API call
    cannot work there at all.
  - No API key ever sits in the page.
  - Playback is instant and offline, which matters when a duel timer runs.
  - You generate once. 102 mora is roughly 200 characters of input.

Two artifacts of synthesising bare mora are handled here directly:
  - An abrupt vowel attack gets heard as a plosive burst (あ mistaken for ぱ).
    Every clip is given a short lead-in silence so the voice eases in rather
    than starting on a hard edge. --pad controls it.
  - Clips that start on the very first sample can be clipped by the browser's
    audio start. The same lead-in covers that.


MALE VOICES
-----------
  google    ja-JP-Neural2-C and ja-JP-Neural2-D are male; A and B are female.
            Chirp3-HD voices are newer and generally better still. Run
            --list-voices to see exactly what your key can reach, with gender.

  say       macOS ships only Kyoko (female) for Japanese by default. The
            standard Japanese MALE voice is Otoya and must be downloaded:
              System Settings > Accessibility > Spoken Content >
              System Voice > Manage Voices > Japanese > Otoya
            Pick Enhanced or Premium while you are there. Once installed,
            Otoya also appears in the game's own voice picker.

  voicevox  Has male character voices (e.g. 玄野武宏, 青山龍星). Free and
            local, but they are character voices and most require a credit
            line -- fine for drilling, less apt as a formal model.


USAGE
-----
  # see what your Google key offers, with gender
  export GOOGLE_TTS_KEY=...
  python3 make_audio_pack.py --list-voices

  # audition several voices on the mora that actually cause trouble
  python3 make_audio_pack.py --compare ja-JP-Neural2-C,ja-JP-Neural2-D,ja-JP-Wavenet-D

  # generate the full pack once you have chosen
  python3 make_audio_pack.py --engine google --voice ja-JP-Neural2-D

  # macOS, after installing Otoya
  python3 make_audio_pack.py --engine say --voice Otoya

Then drag the contents of ./audiopack/ onto "Load recordings..." in the dojo.
"""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAME = HERE / "index.html"
OUT = HERE / "audiopack"

# the mora that expose a weak voice: particles, devoiced onsets, nasals, bare vowel
TROUBLE = ["a", "ha", "he", "wo", "fu", "ku", "su", "tsu", "nu", "ru", "na", "ra", "mu", "n"]


def mora_from_game(path: Path):
    """Pull ["あ","ア","a"] triples straight out of the game's kana table."""
    src = path.read_text(encoding="utf-8")
    start = src.find("const ROWS")
    end = src.find("const BASIC_GROUPS")
    if start == -1 or end == -1:
        sys.exit(f"could not locate the kana table in {path}")
    table = src[start:end]
    seen, out = set(), []
    for hira, _kata, romaji in re.findall(r'\["([^"]+)","([^"]+)","([a-z]+)"', table):
        if romaji in seen:
            continue
        seen.add(romaji)
        out.append((romaji, hira))
    return out


def spoken_form(hira):
    """A lone は / へ / を is normalised to a particle reading by most engines.
    Katakana is never a particle, so it forces the syllabic reading.
    ゐ and ゑ are obsolete; engines guess at them, so pin the modern
    readings /i/ and /e/."""
    return {"は": "ハ", "へ": "ヘ", "を": "ヲ", "ゐ": "イ", "ゑ": "エ"}.get(hira, hira)


def google_key():
    key = os.environ.get("GOOGLE_TTS_KEY")
    if not key:
        sys.exit("set GOOGLE_TTS_KEY to a Google Cloud API key with the "
                 "Text-to-Speech API enabled")
    return key


# ---------------------------------------------------------------- engines


def gen_google(text, dest, args):
    ssml = f'<speak><break time="{int(args.pad * 1000)}ms"/>{text}</speak>'
    body = json.dumps({
        "input": {"ssml": ssml},
        "voice": {"languageCode": "ja-JP", "name": args.voice},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": args.rate},
    }).encode()
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize?key=" + google_key(),
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    dest.with_suffix(".mp3").write_bytes(base64.b64decode(payload["audioContent"]))


def gen_voicevox(text, dest, args):
    base = args.host.rstrip("/")
    q = urllib.request.Request(
        f"{base}/audio_query?speaker={args.speaker}&text=" + urllib.parse.quote(text),
        method="POST")
    with urllib.request.urlopen(q, timeout=30) as r:
        query = json.load(r)
    query["speedScale"] = args.rate
    query["prePhonemeLength"] = args.pad
    query["postPhonemeLength"] = max(args.pad, 0.1)
    syn = urllib.request.Request(
        f"{base}/synthesis?speaker={args.speaker}",
        data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(syn, timeout=60) as r:
        dest.with_suffix(".wav").write_bytes(r.read())


_SAY_VOICES = None


def say_voices():
    global _SAY_VOICES
    if _SAY_VOICES is None:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
        _SAY_VOICES = []
        for line in out.splitlines():
            m = re.match(r"^(.+?)\s{2,}([a-z]{2}_[A-Z]{2})", line)
            if m:
                _SAY_VOICES.append((m.group(1).strip(), m.group(2)))
    return _SAY_VOICES


def check_say_voice(name):
    """macOS `say` accepts ANY voice name, silently substitutes a fallback, and
    exits 0 -- verified: `say -v Otoya` and `say -v MadeUpName` produce
    byte-identical audio when Otoya is not installed. Without this check you
    would generate a whole pack in the wrong voice and never be told."""
    installed = say_voices()
    if any(v == name for v, _ in installed):
        return
    ja = [v for v, lang in installed if lang == "ja_JP"]
    sys.exit(
        f"macOS has no installed voice named {name!r}.\n"
        f"`say` would silently fall back to another voice and you would\n"
        f"generate the entire pack in the wrong voice.\n\n"
        f"Japanese voices installed now: {', '.join(ja) or '(none)'}\n\n"
        f"To add the standard Japanese male voice Otoya:\n"
        f"  System Settings > Accessibility > Spoken Content > System Voice\n"
        f"  > Manage Voices > Japanese > Otoya  (choose Enhanced or Premium)")


def gen_say(text, dest, args):
    # [[slnc N]] inserts N ms of silence, giving the same soft onset
    lead = f"[[slnc {int(args.pad * 1000)}]]"
    aiff = dest.with_suffix(".aiff")
    subprocess.run(
        ["say", "-v", args.voice, "-r", str(int(170 * args.rate)),
         "-o", str(aiff), lead + text],
        check=True)
    if shutil.which("afconvert"):
        subprocess.run(
            ["afconvert", "-f", "mp4f", "-d", "aac",
             str(aiff), str(dest.with_suffix(".m4a"))], check=True)
        aiff.unlink()


ENGINES = {"google": gen_google, "voicevox": gen_voicevox, "say": gen_say}
DEFAULT_VOICE = {"google": "ja-JP-Neural2-D", "say": "Kyoko", "voicevox": ""}


def list_voices():
    url = ("https://texttospeech.googleapis.com/v1/voices?languageCode=ja-JP&key="
           + google_key())
    with urllib.request.urlopen(url, timeout=30) as r:
        voices = json.load(r).get("voices", [])
    voices.sort(key=lambda v: (v.get("ssmlGender", ""), v["name"]))
    print(f"{'voice':<28} {'gender':<8} sample rate")
    print("-" * 52)
    for v in voices:
        print(f"{v['name']:<28} {v.get('ssmlGender','?'):<8} "
              f"{v.get('naturalSampleRateHertz','?')}")
    males = [v["name"] for v in voices if v.get("ssmlGender") == "MALE"]
    print(f"\n{len(voices)} ja-JP voices, {len(males)} male")
    if males:
        print("male: " + ", ".join(males))


def compare(voice_names, args, mora):
    """Render the troublesome mora in each voice, into its own folder."""
    wanted = [m for m in mora if m[0] in set(TROUBLE)]
    root = OUT / "_compare"
    root.mkdir(parents=True, exist_ok=True)
    for name in voice_names:
        args.voice = name
        folder = root / name
        folder.mkdir(exist_ok=True)
        print(f"\n--- {name} ---")
        for romaji, hira in wanted:
            try:
                ENGINES[args.engine](spoken_form(hira), folder / romaji, args)
                print(f"  {romaji}\t{hira}")
            except Exception as e:
                print(f"  {romaji}\t{hira}\tFAILED: {e}", file=sys.stderr)
    print(f"\nWritten to {root}. Listen through each folder and pick a voice, "
          f"then run again with --voice <name>.")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", choices=ENGINES, default="google")
    p.add_argument("--voice", help="engine voice name")
    p.add_argument("--speaker", type=int, default=11, help="voicevox speaker id")
    p.add_argument("--host", default="http://127.0.0.1:50021", help="voicevox host")
    p.add_argument("--rate", type=float, default=1.0, help="speaking rate")
    p.add_argument("--pad", type=float, default=0.15,
                   help="lead-in silence in seconds; softens the vowel attack")
    p.add_argument("--only", help="comma-separated romaji subset, e.g. fu,ku,su,tsu")
    p.add_argument("--trouble", action="store_true",
                   help="generate only the mora that expose a weak voice")
    p.add_argument("--compare", help="comma-separated voices to audition side by side")
    p.add_argument("--list", action="store_true", help="print the mora list and exit")
    p.add_argument("--list-voices", action="store_true",
                   help="list Google ja-JP voices with gender and exit")
    args = p.parse_args()

    if args.list_voices:
        return list_voices()

    if not args.voice:
        args.voice = DEFAULT_VOICE[args.engine]

    mora = mora_from_game(GAME)

    if args.compare:
        names = [v.strip() for v in args.compare.split(",") if v.strip()]
        if args.engine == "say":
            for nm in names:
                check_say_voice(nm)
        return compare(names, args, mora)

    if args.trouble:
        mora = [m for m in mora if m[0] in set(TROUBLE)]
    if args.only:
        want = {s.strip() for s in args.only.split(",") if s.strip()}
        missing = want - {r for r, _ in mora}
        if missing:
            sys.exit("not mora in this game: " + ", ".join(sorted(missing)))
        mora = [m for m in mora if m[0] in want]

    if args.list:
        for romaji, hira in mora:
            print(f"{romaji}\t{hira}\tspoken as {spoken_form(hira)}")
        print(f"\n{len(mora)} clips", file=sys.stderr)
        return

    if args.engine == "say":
        check_say_voice(args.voice)

    OUT.mkdir(exist_ok=True)
    fn = ENGINES[args.engine]
    done = failed = 0
    for i, (romaji, hira) in enumerate(mora, 1):
        try:
            fn(spoken_form(hira), OUT / romaji, args)
            done += 1
            print(f"[{i}/{len(mora)}] {romaji}\t{hira}")
        except Exception as e:                      # keep going; report at the end
            failed += 1
            print(f"[{i}/{len(mora)}] {romaji}\t{hira}\tFAILED: {e}", file=sys.stderr)

    print(f"\n{done} clips written to {OUT}" + (f", {failed} failed" if failed else ""))
    print('Now drag the contents of that folder onto "Load recordings..." in the dojo.')


if __name__ == "__main__":
    main()
