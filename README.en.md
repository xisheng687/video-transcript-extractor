# video-transcript-extractor

[中文](./README.md) | English

A local-first tool for turning online video and social media content into readable transcripts. Give it a video URL or a local media file, and it will extract audio, transcribe it with AI, and write Markdown / TXT transcript files.

The platform extraction layer is powered by [`yt-dlp`](https://github.com/yt-dlp/yt-dlp). The current local `yt-dlp` build includes 1800+ extractors; whenever `yt-dlp` gets stronger for a platform, this tool benefits from that improvement.

## Supported Platforms

Platform extraction mainly relies on the official [`yt-dlp` supported sites list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). The yt-dlp project also notes that websites change constantly, so not every listed extractor is guaranteed to work forever. The most reliable check is to try the URL.

Commonly supported platforms include, but are not limited to:

**Chinese and Asian platforms**

- Bilibili
- Douyin
- Xiaohongshu / RedNote
- AcFun
- Weibo
- Youku
- iQiyi
- Viu
- Niconico
- AbemaTV
- TVer
- NHK

**Global video and livestream platforms**

- YouTube / YouTube Shorts / YouTube Live / YouTube playlists
- TikTok
- Instagram / Reels / Stories
- Facebook / Facebook Reels
- Twitter / X / Spaces
- Vimeo
- Dailymotion
- Twitch
- Rumble
- PeerTube
- BitChute
- LBRY / Odysee

**Social and community content**

- Reddit
- Bluesky
- Pinterest
- LinkedIn
- VK
- Telegram embeds

**Audio, podcast, and music content**

- SoundCloud
- Apple Podcasts
- Ximalaya
- NetEase Cloud Music
- QQ Music
- Bandcamp
- Mixcloud
- Audiomack

**News, education, and media sites**

- BBC
- CNN
- Bloomberg
- NPR
- CCTV
- ABC
- NBC
- Fox News
- TED
- Khan Academy
- Udemy
- ARD
- ZDF
- Arte

Local video or audio files are also supported.

Actual reliability depends on `yt-dlp`, login state, regional availability, and each platform's anti-bot behavior. Some links may require a local `cookies.txt` exported by the user. If `yt-dlp` adds or fixes support for a platform, this tool usually benefits automatically.

## Core Purpose

- Extract audio from video links or local files.
- Convert audio to 64 kbps mono MP3 with `ffmpeg`.
- Transcribe audio with `gemini-2.5-flash`.
- Lightly correct obvious ASR errors with `gemini-2.5-flash-lite`.
- Output Markdown, TXT, raw transcript, and JSON metadata.
- Record token usage, estimated cost, elapsed time, and selected models.

It is designed for personal research, accessibility, knowledge management, and creator workflows. It is not intended for bypassing paywalls, DRM, private content, or platform restrictions.

## Development Notes

This is a simple wrapper, not a new downloader or a new speech recognition model. It connects mature tools into one local workflow:

```text
video URL/local file -> yt-dlp audio extraction -> ffmpeg conversion -> Gemini transcription -> Gemini light cleanup -> transcript output
```

In our own tests on Chinese tech videos, this default model combination had a good cost-quality balance:

- Transcription: `gemini-2.5-flash`
- Cleanup: `gemini-2.5-flash-lite`

For one 13:52 Chinese video, the full workflow cost about `$0.038`, roughly `¥0.27` at `7.2 CNY/USD`. Actual cost varies with duration, speech density, model pricing, and exchange rate.

There are still many limitations. There is no GUI, no built-in batch job manager, and timestamped subtitle output is still basic. Future improvements may include better SRT/VTT output, subtitle-first handling, batch processing, caching, retries, and more model backends.

## Installation

Requirements:

- Python 3.9+
- [`ffmpeg`](https://ffmpeg.org/)
- `yt-dlp`, or [`uv`](https://github.com/astral-sh/uv) so the script can run `uvx yt-dlp`
- A Google Gemini API key

Clone the repo:

```bash
git clone https://github.com/xisheng687/video-transcript-extractor.git
cd video-transcript-extractor
```

Set your API key:

```bash
export GOOGLE_API_KEY="your_google_api_key"
```

Install the optional Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --out-dir ./transcripts
```

If a platform requires login state, pass a local cookie file explicitly:

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --cookies ./cookies.txt \
  --out-dir ./transcripts
```

Local media files also work:

```bash
python3 scripts/extract_video_transcript.py ./example.mp4 \
  --out-dir ./transcripts
```

Each run writes:

- `*-AI高质量校对稿.md`
- `*-transcript.txt`
- `*-raw-transcript.txt`
- `*-metadata.json`
- intermediate audio files under the output `_work/` directory

Do not commit `cookies.txt`, `.env`, API keys, or generated transcripts that may contain private material.

## Using With AI Agents

The easiest workflow is to give this repository URL to Codex CLI, Claude Code, Cursor Agent, or another AI agent and say:

> Please configure this video-to-transcript tool locally. I will provide my own `GOOGLE_API_KEY`.

This repo includes a `SKILL.md`, so agent runtimes that understand Skills can reuse the workflow directly.

## Credits

This project is built on other people's work:

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) is the foundation for video site extraction.
- [`ffmpeg`](https://ffmpeg.org/) handles audio conversion.
- Google Gemini provides the transcription and cleanup models.

Thanks to those maintainers and teams. This repository is only a small wrapper that connects their work into a workflow for Chinese videos and AI agents.

## License

MIT
