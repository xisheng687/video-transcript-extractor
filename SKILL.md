---
name: video-transcript-extractor
description: Extract clean Chinese or multilingual transcripts from video links or local media files. Use when the user provides Bilibili, Douyin, Xiaohongshu, YouTube, TikTok, or other video URLs and asks for a transcript, subtitles, text extraction, video-to-text, ASR, cost estimate, or a reusable workflow.
---

# Video Transcript Extractor

## Default Workflow

Use `scripts/extract_video_transcript.py` for repeatable extraction. It:

1. Uses `yt-dlp` to download audio from a URL, or accepts a local media/audio file.
2. Converts audio to 64 kbps mono MP3 with `ffmpeg`.
3. Splits long audio into chunks.
4. Transcribes with Google Gemini 2.5 Flash, with `thinkingBudget=0`.
5. Lightly corrects the transcript with Gemini 2.5 Flash Lite.
6. Writes Markdown, TXT, JSON metadata, intermediate audio, and cost estimates.

Run from the repository root:

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL_OR_LOCAL_FILE" --out-dir ./transcripts
```

The script reads `GOOGLE_API_KEY` from the environment, or from `~/.agents/secrets/.env`.
Do not print API keys, cookies, or authorization headers.

## Model Choice

Default:

- Transcription: `gemini-2.5-flash`
- Text polish: `gemini-2.5-flash-lite`

Use OpenRouter only as an optional fallback after checking that the selected
model and provider route are available for the user's key.

## Platform Notes

`yt-dlp` is the first choice for YouTube, Bilibili, Douyin, Xiaohongshu, TikTok,
and many other sites. If a URL requires login, region access, or anti-bot checks,
ask the user for a local cookie file only when needed. Never upload or print
cookies.

If a platform provides official subtitles, prefer downloading subtitles first.
If there are no usable subtitles, extract audio and run Gemini ASR.

## Output Guidance

Return the final Markdown transcript path and a short cost summary. Mention that
AI transcripts may still need human review for proper nouns and technical terms.

If the user asks for a publish-ready transcript, run a second light proofreading
pass, but do not rewrite arguments or add new content.

## Cost Formula

The script uses these pricing constants from the tested workflow:

- Gemini 2.5 Flash audio input: `$1.00 / 1M audio tokens`
- Gemini 2.5 Flash text input: `$0.30 / 1M text tokens`
- Gemini 2.5 Flash output: `$2.50 / 1M output tokens`
- Gemini 2.5 Flash Lite text input: `$0.10 / 1M text tokens`
- Gemini 2.5 Flash Lite output: `$0.40 / 1M output tokens`

For a tested 13:52 Bilibili video, the full workflow cost was about `$0.038`,
roughly `¥0.27` at `7.2 CNY/USD`.

## When To Avoid

Do not use this skill to bypass paywalls, private videos, DRM, or account
restrictions. Keep it for user-authorized research, accessibility, summarization,
and personal knowledge workflows.
