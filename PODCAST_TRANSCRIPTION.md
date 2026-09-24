# Podcast transcript workflow

The app can read plain text, SRT, or VTT transcripts. Full transcripts remain in the browser's local draft and are not added to `ev_db` or committed to this repository.

## One-time setup

```sh
brew install ffmpeg
python3 -m pip install -U openai-whisper
```

## Episode 3: official RSS

```sh
python3 transcribe_podcast.py --preset episode3
```

The generated `.srt` or `.txt` file will be in `transcript_work/`. Open it, copy the text, and paste it into **Transcriptから追加** in the app.

## Episode 1: local audio

No public official RSS source has been identified for episode 1. If the publisher gives you an audio download, or you otherwise have an audio file you are permitted to use, run:

```sh
python3 transcribe_podcast.py --audio "/path/to/episode-1.mp3"
```

The helper intentionally does not download from or bypass Spotify. Keep audio and full transcripts private; `transcript_work/` is ignored by Git.

## Any future official podcast RSS

```sh
python3 transcribe_podcast.py \
  --rss "https://publisher.example/podcast.rss" \
  --title "Exact episode title"
```

For YouTube, use its built-in transcript when available, or download/export audio only where you have permission, then use `--audio`.
