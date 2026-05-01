# video-transcript-extractor

中文 | [English](./README.en.md)

一个本地优先的视频链接转文字稿工具。输入视频链接或本地媒体文件，它会提取音频、调用 AI 转写，再生成更适合阅读和整理的 Markdown / TXT 文字稿。

## 支持平台

平台解析主要依赖 [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)，因此理论上支持 `yt-dlp` 已覆盖的大量视频网站。这个工具主要面向这些常见平台：

- YouTube
- Bilibili / 哔哩哔哩
- Douyin / 抖音
- Xiaohongshu / 小红书
- TikTok
- 其他 `yt-dlp` 支持的视频链接
- 本地视频或音频文件

不同平台的稳定性取决于 `yt-dlp`、登录状态、地区限制和平台风控。有些链接可能需要你自己导出的本地 `cookies.txt`。

## 核心作用

- 从视频链接或本地文件提取音频。
- 用 `ffmpeg` 转成适合模型处理的 64 kbps 单声道 MP3。
- 用 `gemini-2.5-flash` 进行音频转写。
- 用 `gemini-2.5-flash-lite` 做轻量校对，修正常见错字、术语和标点。
- 输出 Markdown、TXT、原始转写稿和 JSON 元数据。
- 在元数据中记录 token 用量、估算成本、耗时和使用模型。

它适合个人研究、无障碍阅读、知识管理、内容创作者整理素材。不适合用来绕过付费墙、DRM、私密内容或平台访问限制。

## 开发说明

这个项目本身很简单，没有发明新的下载器，也没有发明新的语音识别模型。它做的事情是把几个成熟工具串成一个更顺手的本地流程：

```text
视频链接/本地文件 -> yt-dlp 提取音频 -> ffmpeg 转码 -> Gemini 转写 -> Gemini 轻量校对 -> 输出文字稿
```

我们自己测试了一些中文科技视频，发现当前默认组合的性价比较好：

- 音频转写：`gemini-2.5-flash`
- 文本校对：`gemini-2.5-flash-lite`

一条 13 分 52 秒的中文视频，完整流程实测成本约 `$0.038`，按 `7.2 CNY/USD` 约 `¥0.27`。实际成本会随视频时长、语速、音频密度、模型价格和汇率变化。

目前它还有很多不足，比如没有完整的 GUI，没有内置批量任务管理，字幕时间轴能力也还比较基础。后续可以继续改进 SRT/VTT 输出、字幕优先策略、批量处理、缓存、失败重试和更多模型后端。

## 安装

需要：

- Python 3.9+
- [`ffmpeg`](https://ffmpeg.org/)
- `yt-dlp`，或者安装 [`uv`](https://github.com/astral-sh/uv)，让脚本通过 `uvx yt-dlp` 自动调用
- 一个 Google Gemini API key

克隆仓库：

```bash
git clone https://github.com/xisheng687/video-transcript-extractor.git
cd video-transcript-extractor
```

设置 API key：

```bash
export GOOGLE_API_KEY="your_google_api_key"
```

安装可选 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

## 使用

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --out-dir ./transcripts
```

如果平台需要登录态，可以显式传入本地 cookie 文件：

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --cookies ./cookies.txt \
  --out-dir ./transcripts
```

也可以处理本地文件：

```bash
python3 scripts/extract_video_transcript.py ./example.mp4 \
  --out-dir ./transcripts
```

每次运行会输出：

- `*-AI高质量校对稿.md`
- `*-transcript.txt`
- `*-raw-transcript.txt`
- `*-metadata.json`
- 中间音频文件，位于输出目录的 `_work/` 下

不要提交 `cookies.txt`、`.env`、API key，或包含隐私内容的生成稿。

## 给 AI Agent 使用

更简单的方式是直接把这个仓库链接发给 Codex CLI、Claude Code、Cursor Agent、龙虾之类的 AI Agent，然后说：

> 帮我把这个视频转文字稿工具配置好，我会自己提供 `GOOGLE_API_KEY`。

这个仓库包含 `SKILL.md`，支持 Skill 的 Agent 可以直接读取并复用这个流程。

## 致谢

这个项目建立在前人工作的基础上：

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) 是多平台视频提取的基础。
- [`ffmpeg`](https://ffmpeg.org/) 负责音频转换。
- Google Gemini 提供转写和校对模型。

感谢这些项目和团队。这个仓库只是一个很小的包装，把它们串成一个适合中文视频和 AI Agent 使用的流程。

## License

MIT
