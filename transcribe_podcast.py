#!/usr/bin/env python3
"""Download an episode from an official RSS feed, then transcribe it with Whisper.

The audio and generated transcript stay in transcript_work/, which is ignored by Git.
This script does not access or bypass Spotify media delivery.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


PRESETS = {
    "episode2": {
        "rss": "https://www.omnycontent.com/d/playlist/de62ff84-6498-49d0-a266-a9d50120c712/189fdf10-6536-441e-95bb-ad1e0053c01b/86a98568-05bc-4c07-8288-ad1e0054f2f2/podcast.rss",
        "title": "Sabah For Sabahans: Understanding MA63, Project IC and Federal-State Tensions",
    },
    "episode3": {
        "rss": "https://www.omnycontent.com/d/playlist/de62ff84-6498-49d0-a266-a9d50120c712/348bcb36-1085-4351-a720-ab0900403779/962d774e-ec4d-4ac7-89ad-ab090040377e/podcast.rss",
        "title": "Solutions For Stateless In Sabah?",
    },
}


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return value[:80] or "podcast-episode"


def fetch_bytes(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are supported.")
    request = urllib.request.Request(url, headers={"User-Agent": "EnglishVocab/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def find_enclosure(rss_url: str, wanted_title: str) -> tuple[str, str]:
    root = ET.fromstring(fetch_bytes(rss_url))
    wanted = wanted_title.casefold().strip()
    exact = None
    partial = None
    available = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        enclosure = item.find("enclosure")
        url = enclosure.get("url", "").strip() if enclosure is not None else ""
        if not title or not url:
            continue
        available.append(title)
        candidate = (title, url)
        folded = title.casefold()
        if folded == wanted:
            exact = candidate
            break
        if wanted in folded or folded in wanted:
            partial = candidate
    if exact:
        return exact
    if partial:
        return partial
    preview = "\n  - ".join(available[:12])
    raise RuntimeError(f"Episode title not found in RSS. Recent titles:\n  - {preview}")


def download_audio(url: str, title: str, output_dir: Path) -> Path:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if suffix not in {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".mp4"}:
        suffix = ".mp3"
    target = output_dir / f"{slugify(title)}{suffix}"
    if target.exists() and target.stat().st_size:
        print(f"Using existing audio: {target}")
        return target
    print(f"Downloading official RSS enclosure:\n  {title}\n  -> {target}")
    request = urllib.request.Request(url, headers={"User-Agent": "EnglishVocab/1.0"})
    partial = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output)
    partial.replace(target)
    return target


def transcribe(audio: Path, output_dir: Path, model: str, language: str) -> None:
    whisper = shutil.which("whisper")
    ffmpeg = shutil.which("ffmpeg")
    if not whisper or not ffmpeg:
        missing = ", ".join(name for name, path in (("whisper", whisper), ("ffmpeg", ffmpeg)) if not path)
        raise RuntimeError(
            f"Missing: {missing}. Install with `brew install ffmpeg` and "
            "`python3 -m pip install -U openai-whisper`."
        )
    command = [
        whisper,
        str(audio),
        "--model",
        model,
        "--language",
        language,
        "--task",
        "transcribe",
        "--output_format",
        "all",
        "--output_dir",
        str(output_dir),
    ]
    print("Starting local transcription. This can take a while...")
    subprocess.run(command, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe an official podcast RSS episode or a local audio file with Whisper."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--preset", choices=sorted(PRESETS), help="Known episode in this project")
    source.add_argument("--audio", type=Path, help="Local audio file you are allowed to use")
    source.add_argument("--rss", help="Official podcast RSS URL")
    parser.add_argument("--title", help="Episode title to find when using --rss")
    parser.add_argument("--output-dir", type=Path, default=Path("transcript_work"))
    parser.add_argument("--model", default="turbo", help="Whisper model (default: turbo)")
    parser.add_argument("--language", default="English", help="Spoken language (default: English)")
    parser.add_argument("--download-only", action="store_true", help="Download RSS audio without transcription")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.preset:
        rss_url = PRESETS[args.preset]["rss"]
        title = PRESETS[args.preset]["title"]
        found_title, enclosure = find_enclosure(rss_url, title)
        audio = download_audio(enclosure, found_title, args.output_dir)
    elif args.rss:
        if not args.title:
            raise RuntimeError("--title is required with --rss.")
        found_title, enclosure = find_enclosure(args.rss, args.title)
        audio = download_audio(enclosure, found_title, args.output_dir)
    else:
        audio = args.audio.expanduser().resolve()
        if not audio.is_file():
            raise RuntimeError(f"Audio file not found: {audio}")
    if not args.download_only:
        transcribe(audio, args.output_dir.resolve(), args.model, args.language)
        print(f"Done. Paste the generated .srt or .txt into the app:\n  {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, ET.ParseError, urllib.error.URLError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
