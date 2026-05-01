# Security Policy

## Sensitive Data

This project may process video/audio content, generated transcripts, cookies, and API keys.

- Do not publish API keys, cookie files, private media, signed URLs, or generated transcripts that contain private material.
- The tool sends audio chunks and raw transcript text to Google Gemini. Review Google's data and API terms before processing confidential content.
- Output files redact URL query strings, fragments, and local paths by default. Use `--include-source` only when you intentionally want exact sources in outputs.

## Reporting A Vulnerability

Please open a GitHub issue with a minimal description that does not include secrets, cookies, private URLs, or private media. If a report requires sensitive details, first open an issue asking for a private contact path.

## Supported Versions

Only the latest `main` branch is currently supported.
