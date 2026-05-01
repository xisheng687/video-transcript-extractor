# video-transcript-extractor

中文 | [English](./README.en.md)

一个很小的、本地优先的视频链接转文字稿工具。

先说清楚：这个项目没有多少原创技术含量。它本质上只是把几个优秀的现有工具串成一个可重复使用的流程。它不是新的下载器，不是新的语音模型，也不是绕过平台限制的工具。真正的基础工作来自：

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)：负责视频平台的元数据、字幕和音频提取。
- [`ffmpeg`](https://ffmpeg.org/)：负责可靠的音频转换。
- Google Gemini API：负责音频转写和轻量文本校对。

这个仓库做的事情很朴素：给一个视频链接，得到一份更干净的 Markdown 文字稿，同时给出大致成本估算，并提供一个适合 Codex / Claude Code / AI Agent 使用的 Skill 包装。

## 它能做什么

- 接受视频 URL 或本地媒体/音频文件。
- 用 `yt-dlp` 提取音频。
- 用 `ffmpeg` 转成 64 kbps 单声道 MP3。
- 用 `gemini-2.5-flash` 做音频转写。
- 用 `gemini-2.5-flash-lite` 做明显错字和术语的轻量校对。
- 输出 Markdown、TXT、原始转写稿、JSON 元数据。
- JSON 元数据里会包含 token 用量和估算成本。

它适合个人研究、无障碍阅读、知识管理、内容创作者整理素材。不适合用来绕过付费墙、DRM、私密内容或平台访问限制。

## 为什么做这个

能下载媒体的工具很多，能语音转文字的模型也很多。麻烦的是把它们稳定地串起来，尤其是中文视频经常会遇到：

- B站、抖音、小红书、YouTube 等平台体验不统一。
- 有些视频有字幕，有些没有，只能抽音频做 ASR。
- 原始 ASR 文本可读性差，需要标点、分段、术语校对。
- API key 和 cookie 不能乱传、不能泄漏。
- 调用云端模型最好能知道大概花了多少钱。

这个项目就是把这些步骤收拢成一个本地脚本和一个 Agent Skill。

## API 推荐

我们自己测试过一条 13 分 52 秒的中文科技视频，当前性价比较好的默认组合是：

- 音频转写：`gemini-2.5-flash`
- 文本校对：`gemini-2.5-flash-lite`

这条视频完整流程实测成本约 `$0.038`，按 `7.2 CNY/USD` 约 `¥0.27`。实际成本会随视频时长、语速、音频密度、模型价格和汇率变化。

脚本里可以替换模型或服务商。OpenAI 的转写模型也可能很好，但在我们的测试环境里，Google Gemini 直连比通过 OpenRouter 路由音频更便宜、更稳定。

## 依赖

- Python 3.9+
- [`ffmpeg`](https://ffmpeg.org/)
- `yt-dlp`，或者安装 [`uv`](https://github.com/astral-sh/uv)，让脚本通过 `uvx yt-dlp` 自动调用
- 一个 Google Gemini API key

可选：

- `opencc-python-reimplemented`：用于繁体转简体兜底处理。

## 快速开始

克隆仓库后，设置你的 API key：

```bash
export GOOGLE_API_KEY="your_google_api_key"
```

安装可选 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

运行：

```bash
python3 scripts/extract_video_transcript.py "https://www.youtube.com/watch?v=..." \
  --out-dir ./transcripts
```

B站、抖音、小红书、TikTok 或其他 `yt-dlp` 支持的平台也一样传 URL。平台支持取决于 `yt-dlp`，部分登录/地区/风控内容可能需要你自己导出的本地 `cookies.txt`：

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --cookies ./cookies.txt \
  --out-dir ./transcripts
```

不要提交 `cookies.txt`、`.env`、API key，或包含隐私内容的生成稿。

## 给 AI Agent 使用

现在更简单的方式是直接把这个仓库链接发给 Codex CLI、Claude Code、Cursor Agent、龙虾之类的 AI Agent，然后说：

> 帮我把这个视频转文字稿工具配置好，我会自己提供 `GOOGLE_API_KEY`。

这个仓库包含 `SKILL.md`，支持 Skill 的 Agent 可以直接读取并复用这个流程。API key 仍然需要你自己申请并填入本地环境变量。

## 输出文件

每次运行会输出：

- `*-AI高质量校对稿.md`
- `*-transcript.txt`
- `*-raw-transcript.txt`
- `*-metadata.json`
- 中间音频文件，位于输出目录的 `_work/` 下

`metadata.json` 会记录视频时长、使用模型、token 用量、估算美元/人民币成本、耗时等信息。

## 隐私与安全

- API key 从 `GOOGLE_API_KEY` 或 `~/.agents/secrets/.env` 读取。
- 脚本不会主动打印 API key。
- cookie 只有在你显式传入 `--cookies` 时才会使用。
- 不要处理你无权访问或无权转写的内容。
- 视频文字稿可能属于原视频的衍生文本。除非你有权利再分发，否则请把它当作个人研究、无障碍阅读或知识管理材料。

## 致谢

这个项目站在前人的基础上：

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) 是多平台视频提取的基础。
- [`ffmpeg`](https://ffmpeg.org/) 负责音频转换。
- Google Gemini 提供转写和校对模型。

感谢这些项目和团队。这个仓库只是一个很小、很本分的包装，把他们的工作串成一个适合中文视频和 AI Agent 使用的流程。

## License

MIT
