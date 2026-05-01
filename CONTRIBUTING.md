# Contributing

Thanks for helping improve this project.

## Development

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Run the basic checks:

```bash
python3 -m py_compile scripts/extract_video_transcript.py
python3 scripts/extract_video_transcript.py --help
```

3. Keep changes focused and avoid committing generated transcripts, cookies, media files, or API keys.

## Pull Requests

- Explain what changed and why.
- Mention whether the change affects privacy, provider calls, metadata, or generated output.
- Add or update documentation when command-line behavior changes.
- Do not include private URLs, cookies, API keys, or generated transcripts in issues or pull requests.
