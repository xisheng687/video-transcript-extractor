# video-transcript-extractor

A small, local-first bridge that turns video links into clean transcripts.

This project is intentionally modest. There is very little original technical
novelty here: it mainly connects existing tools into one repeatable workflow. It
is not a new downloader, a new speech model, or a clever bypass. The core work
is done by excellent existing tools:

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) for extracting metadata, subtitles,
  and audio from video platforms.
- [`ffmpeg`](https://ffmpeg.org/) for reliable audio conversion.
- Google Gemini API for audio transcription and light transcript cleanup.

What this repo adds is a practical workflow around those pieces: video URL in,
clean Markdown transcript out, with a cost estimate and a Codex/agent-friendly
Skill wrapper.

## What It Does

- Accepts a video URL or local media/audio file.
- Uses `yt-dlp` to extract audio.
- Converts audio to 64 kbps mono MP3 with `ffmpeg`.
- Transcribes audio with `gemini-2.5-flash`.
- Lightly corrects obvious ASR errors with `gemini-2.5-flash-lite`.
- Outputs Markdown, TXT, raw transcript, and JSON metadata with token usage and
  estimated cost.

It is designed for personal research, accessibility, knowledge management, and
creator workflows. It is not intended for bypassing paywalls, DRM, private
content, or platform restrictions.

## Why This Exists

Many tools can download media. Many models can transcribe audio. The annoying
part is wiring them together in a repeatable, Chinese-friendly workflow that:

- Works across common platforms handled by `yt-dlp`, such as YouTube, Bilibili,
  Douyin, Xiaohongshu, TikTok, and many more.
- Handles videos without official subtitles by falling back to audio ASR.
- Gives a readable transcript instead of a raw line-by-line dump.
- Keeps API keys and cookies local.
- Shows approximate cost.

## API Recommendation

In our own test on a 13:52 Chinese tech video, the best cost-quality default was:

- Transcription: `gemini-2.5-flash`
- Cleanup: `gemini-2.5-flash-lite`

Observed cost for the full workflow was about `$0.038`, roughly `¥0.27` at
`7.2 CNY/USD`. Your cost will vary with duration, audio density, model pricing,
and exchange rate.

You can swap models or providers in the script. OpenAI transcription models may
also work well, but in our test environment Gemini direct API was cheaper and
more reliable than routing audio through OpenRouter.

## Requirements

- Python 3.9+
- [`ffmpeg`](https://ffmpeg.org/)
- `yt-dlp`, or [`uv`](https://github.com/astral-sh/uv) so the script can run
  `uvx yt-dlp`
- A Google Gemini API key

Optional:

- `opencc-python-reimplemented` for traditional-to-simplified Chinese cleanup.

## Quick Start

Clone this repo, then set your API key:

```bash
export GOOGLE_API_KEY="your_google_api_key"
```

Install optional Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

Run:

```bash
python3 scripts/extract_video_transcript.py "https://www.youtube.com/watch?v=..." \
  --out-dir ./transcripts
```

For a Bilibili, Douyin, Xiaohongshu, TikTok, or other supported URL, pass the
URL the same way. Platform support depends on `yt-dlp`, and some URLs may require
a local `cookies.txt` file:

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --cookies ./cookies.txt \
  --out-dir ./transcripts
```

Never commit `cookies.txt`, `.env`, API keys, or generated transcripts that may
contain private material.

## Using With AI Agents

The easiest AI-agent-era workflow is:

1. Give this repository URL to Codex CLI, Claude Code, or your preferred agent.
2. Ask it to install/configure the tool locally.
3. Provide your own `GOOGLE_API_KEY`.
4. Send video links to the agent and ask it to run the transcript extractor.

This repo includes a `SKILL.md` so agent runtimes that understand Skills can
reuse the workflow directly.

## Outputs

For each input, the script writes:

- `*-AI高质量校对稿.md`
- `*-transcript.txt`
- `*-raw-transcript.txt`
- `*-metadata.json`
- intermediate audio files under the output `_work/` directory

The metadata JSON includes duration, models, token usage, estimated USD/CNY cost,
and elapsed time.

## Privacy And Safety

- API keys are read from `GOOGLE_API_KEY` or `~/.agents/secrets/.env`.
- API keys are never printed intentionally.
- Cookies are used only when explicitly passed with `--cookies`.
- Do not use this tool for content you are not allowed to access or process.
- Transcripts may be derivative text from copyrighted videos. Treat them as
  personal research or accessibility artifacts unless you have the right to
  redistribute them.

## Credits

This project stands on other people's work:

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) is the foundation for video site
  extraction.
- [`ffmpeg`](https://ffmpeg.org/) handles audio conversion.
- Google Gemini provides the transcription and cleanup models.

Thank you to those maintainers and teams. This repository is just a small,
opinionated wrapper around their much more substantial work.

## License

MIT
