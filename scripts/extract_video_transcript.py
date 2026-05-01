#!/usr/bin/env python3
"""Extract and polish transcripts from video URLs or local media files.

This script is intentionally local-first:
- no API keys are logged
- cookies are used only when explicitly supplied
- provider usage and estimated costs are written to metadata JSON
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

FLASH_AUDIO_IN_PER_M = 1.00
FLASH_TEXT_IN_PER_M = 0.30
FLASH_OUT_PER_M = 2.50
LITE_TEXT_IN_PER_M = 0.10
LITE_OUT_PER_M = 0.40


TRANSCRIBE_PROMPT = """请逐字转写这段视频音频。
要求：
1. 只输出文字稿，不要总结，不要添加原音频没有的观点。
2. 使用简体中文；保留英文术语、缩写、公司名、技术名。
3. 中文标点自然分段。
4. 如果某个词听不清，尽量根据上下文判断，但不要硬编。

术语参考：
{terms}
"""


POLISH_PROMPT = """你是中文科技视频文字稿校对员。请对下面的自动转写稿做轻量校对：
- 只修正明显错别字、术语、人名/机构名/英文缩写、标点和简繁残留。
- 不要总结，不要改写观点，不要增删段落内容。
- 保持简体中文。
- 只输出校对后的完整文字稿。

术语参考：
{terms}

自动转写稿如下：
{transcript}
"""


DEFAULT_TERMS = (
    "Hyperoperation System, tetration, Recursive Self-Improvement, AI native, "
    "AI Native Economy, Agent, Harness, Tool Integration, Long-term Memory, "
    "OpenAI, Sam Altman, Stanford HAI, NVIDIA, Huang Renxun, Rubin, GPU, CPU, "
    "HBM4, LPU, EUV, GDP, Future of Life Institute, Electronic Frontier Foundation"
)


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def load_env_value(name: str, env_file: Path = Path("~/.agents/secrets/.env").expanduser()) -> str:
    if os.environ.get(name):
        return os.environ[name]
    if not env_file.exists():
        return ""
    for raw_line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != name:
            continue
        try:
            parts = shlex.split(value, comments=False, posix=True)
            return parts[0] if parts else ""
        except ValueError:
            return value.strip().strip("\"'")
    return ""


def slugify(value: str, fallback: str = "video") -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "-", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:80] or fallback


def ytdlp_cmd() -> list[str]:
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    if shutil.which("uvx"):
        return ["uvx", "yt-dlp"]
    raise SystemExit("yt-dlp is not installed and uvx is unavailable.")


def get_media_title(source: str) -> str:
    if Path(source).exists():
        return Path(source).stem
    try:
        proc = run(ytdlp_cmd() + ["--no-playlist", "--dump-json", source])
        data = json.loads(proc.stdout)
        return data.get("title") or data.get("id") or "video"
    except Exception:
        return "video"


def download_audio(source: str, work_dir: Path, base_name: str, cookies: str | None) -> Path:
    source_path = Path(source)
    if source_path.exists():
        return source_path

    out_tpl = str(work_dir / f"{base_name}.download.%(ext)s")
    base_cmd = ytdlp_cmd()
    cmd = base_cmd + [
        "--no-playlist",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "64K",
        "-o",
        out_tpl,
        source,
    ]
    if cookies:
        insert_at = len(base_cmd)
        cmd[insert_at:insert_at] = ["--cookies", cookies]
    run(cmd)
    candidates = sorted(work_dir.glob(f"{base_name}.download.*"))
    if not candidates:
        raise SystemExit("yt-dlp finished but no audio file was found.")
    return candidates[-1]


def convert_to_mp3(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() == ".mp3":
        if input_path.resolve() != output_path.resolve():
            shutil.copyfile(input_path, output_path)
        return output_path
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "64k",
            str(output_path),
        ]
    )
    return output_path


def duration_seconds(media: Path) -> float:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media),
        ]
    )
    return float(proc.stdout.strip())


def split_audio(media: Path, chunk_dir: Path, chunk_seconds: int) -> list[Path]:
    total = duration_seconds(media)
    if total <= chunk_seconds:
        return [media]
    chunk_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(chunk_dir / "chunk_%03d.mp3")
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(media),
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-c",
            "copy",
            pattern,
        ]
    )
    return sorted(chunk_dir.glob("chunk_*.mp3"))


def gemini_generate(api_key: str, model: str, payload: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=model),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore")
        raise RuntimeError(f"Gemini API error {exc.code}: {body[:1000]}") from exc


def response_text(data: dict) -> str:
    return "".join(
        part.get("text", "")
        for candidate in data.get("candidates", [])
        for part in candidate.get("content", {}).get("parts", [])
    ).strip()


def usage_cost_transcribe(usage: dict) -> float:
    audio_tokens = 0
    text_tokens = 0
    for item in usage.get("promptTokensDetails", []):
        if item.get("modality") == "AUDIO":
            audio_tokens += item.get("tokenCount", 0)
        elif item.get("modality") == "TEXT":
            text_tokens += item.get("tokenCount", 0)
    output_tokens = usage.get("candidatesTokenCount", 0)
    return (
        audio_tokens * FLASH_AUDIO_IN_PER_M / 1_000_000
        + text_tokens * FLASH_TEXT_IN_PER_M / 1_000_000
        + output_tokens * FLASH_OUT_PER_M / 1_000_000
    )


def usage_cost_polish(usage: dict) -> float:
    return (
        usage.get("promptTokenCount", 0) * LITE_TEXT_IN_PER_M / 1_000_000
        + usage.get("candidatesTokenCount", 0) * LITE_OUT_PER_M / 1_000_000
    )


def simplify_chinese(text: str) -> str:
    try:
        from opencc import OpenCC  # type: ignore

        return OpenCC("t2s").convert(text)
    except Exception:
        return text


def transcribe_chunk(api_key: str, chunk: Path, model: str, terms: str, index: int, total: int) -> tuple[str, dict]:
    audio_b64 = base64.b64encode(chunk.read_bytes()).decode("ascii")
    prompt = TRANSCRIBE_PROMPT.format(terms=terms)
    if total > 1:
        prompt += f"\n这是第 {index + 1}/{total} 段音频。只转写本段。"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "audio/mpeg", "data": audio_b64}},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 8192,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    data = gemini_generate(api_key, model, payload)
    return simplify_chinese(response_text(data)), data


def polish_text(api_key: str, text: str, model: str, terms: str) -> tuple[str, list[dict]]:
    # Split conservatively by characters to avoid output caps on long videos.
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        candidate_len = len(paragraph) + 2
        if current and current_len + candidate_len > 10_000:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += candidate_len
    if current:
        chunks.append("\n\n".join(current))

    outputs: list[str] = []
    raw: list[dict] = []
    for chunk in chunks:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": POLISH_PROMPT.format(terms=terms, transcript=chunk)}],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 9000,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        data = gemini_generate(api_key, model, payload)
        raw.append(data)
        outputs.append(simplify_chinese(response_text(data)))
    return "\n\n".join(outputs).strip(), raw


def write_outputs(
    out_dir: Path,
    title: str,
    source: str,
    transcript: str,
    raw_transcript: str,
    metadata: dict,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = slugify(title)
    md = (
        f"# {title}\n\n"
        f"- 来源：{source}\n"
        f"- 提取方式：Gemini 2.5 Flash 音频转写 + Gemini 2.5 Flash Lite 文本校对\n"
        f"- 说明：AI 自动转写与轻量校对，未做逐字人工校对。\n\n"
        "## 文字稿\n\n"
        f"{transcript.strip()}\n"
    )
    (out_dir / f"{safe}-AI高质量校对稿.md").write_text(md, encoding="utf-8")
    (out_dir / f"{safe}-transcript.txt").write_text(transcript.strip() + "\n", encoding="utf-8")
    (out_dir / f"{safe}-raw-transcript.txt").write_text(raw_transcript.strip() + "\n", encoding="utf-8")
    (out_dir / f"{safe}-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(out_dir / f"{safe}-AI高质量校对稿.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a polished transcript from a video URL or local media file.")
    parser.add_argument("source", help="Video URL or local media/audio file")
    parser.add_argument("--out-dir", default="./transcripts", help="Output directory")
    parser.add_argument("--title", help="Override output title")
    parser.add_argument("--cookies", help="Optional local cookies.txt for yt-dlp")
    parser.add_argument("--chunk-seconds", type=int, default=600, help="Audio chunk size for Gemini")
    parser.add_argument("--terms", default=DEFAULT_TERMS, help="Comma-separated/domain terms to bias transcription")
    parser.add_argument("--transcribe-model", default="gemini-2.5-flash")
    parser.add_argument("--polish-model", default="gemini-2.5-flash-lite")
    parser.add_argument("--usd-to-cny", type=float, default=7.2)
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe are required.")

    api_key = load_env_value("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY is missing. Set it in the environment or ~/.agents/secrets/.env.")

    out_dir = Path(args.out_dir).expanduser().resolve()
    work_dir = out_dir / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or get_media_title(args.source)
    base_name = slugify(title)
    started = time.time()

    input_audio = download_audio(args.source, work_dir, base_name, args.cookies)
    mp3_path = convert_to_mp3(input_audio, work_dir / f"{base_name}.64k.mp3")
    chunks = split_audio(mp3_path, work_dir / f"{base_name}.chunks", args.chunk_seconds)

    raw_parts: list[str] = []
    transcribe_responses: list[dict] = []
    transcribe_cost = 0.0
    for i, chunk in enumerate(chunks):
        text, data = transcribe_chunk(api_key, chunk, args.transcribe_model, args.terms, i, len(chunks))
        raw_parts.append(text)
        transcribe_responses.append(data)
        transcribe_cost += usage_cost_transcribe(data.get("usageMetadata", {}))

    raw_transcript = "\n\n".join(raw_parts).strip()
    polished, polish_responses = polish_text(api_key, raw_transcript, args.polish_model, args.terms)
    polish_cost = sum(usage_cost_polish(item.get("usageMetadata", {})) for item in polish_responses)

    metadata = {
        "source": args.source,
        "title": title,
        "duration_seconds": duration_seconds(mp3_path),
        "chunks": [str(path) for path in chunks],
        "models": {
            "transcribe": args.transcribe_model,
            "polish": args.polish_model,
        },
        "usage": {
            "transcribe": [item.get("usageMetadata", {}) for item in transcribe_responses],
            "polish": [item.get("usageMetadata", {}) for item in polish_responses],
        },
        "estimated_cost_usd": {
            "transcribe": round(transcribe_cost, 6),
            "polish": round(polish_cost, 6),
            "total": round(transcribe_cost + polish_cost, 6),
        },
        "estimated_cost_cny": round((transcribe_cost + polish_cost) * args.usd_to_cny, 4),
        "elapsed_seconds": round(time.time() - started, 2),
    }
    write_outputs(out_dir, title, args.source, polished, raw_transcript, metadata)

    print(
        json.dumps(
            {
                "estimated_cost_usd": metadata["estimated_cost_usd"]["total"],
                "estimated_cost_cny": metadata["estimated_cost_cny"],
                "elapsed_seconds": metadata["elapsed_seconds"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
