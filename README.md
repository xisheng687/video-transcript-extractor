# video-transcript-extractor

中文 | [English](./README.en.md)

一个本地编排优先的在线视频/社媒内容转文字稿工具。输入一个视频链接或本地媒体文件，它会在本机提取和转码音频，然后调用 Google Gemini 做语音转文字和轻量校对，生成更适合阅读和整理的 Markdown / TXT 文字稿。

它的底层平台解析能力来自 [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)。当前 `yt-dlp` 本地版本包含 1800+ 个 extractor；只要 `yt-dlp` 对某个平台支持得更好，这个工具的可用范围也会跟着变强。

## 支持平台

平台解析主要依赖 [`yt-dlp` 官方支持列表](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)。官方也说明，网站经常变化，并非列表里的每个站点都永久保证可用；最可靠的判断方式是实际跑一次。

常见可用平台包括但不限于：

**中文与亚洲平台**

- Bilibili / 哔哩哔哩
- Douyin / 抖音
- Xiaohongshu / 小红书
- AcFun
- Weibo / 微博
- Youku / 优酷
- iQiyi / 爱奇艺
- Viu
- Niconico
- AbemaTV
- TVer
- NHK

**全球视频与直播平台**

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

**社媒与社区内容**

- Reddit
- Bluesky
- Pinterest
- LinkedIn
- VK
- Telegram embeds

**音频、播客与音乐内容**

- SoundCloud
- Apple Podcasts
- Ximalaya / 喜马拉雅
- NetEase Cloud Music / 网易云音乐
- QQ Music / QQ 音乐
- Bandcamp
- Mixcloud
- Audiomack

**新闻、教育与媒体站点**

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

此外，也支持本地视频或音频文件。

不同平台的稳定性取决于 `yt-dlp`、登录状态、地区限制和平台风控。有些链接可能需要你自己导出的本地 `cookies.txt`。如果 `yt-dlp` 未来新增或修复了某个平台，这个工具通常也能直接受益。

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

## 隐私与费用

- 本工具不会打印 API key，也不会自动读取全局密钥文件。
- 音频片段会发送到 Google Gemini API 做转写；原始转写文本会再次发送到 Gemini 做轻量校对。
- 如果传入 `--cookies`，cookie 文件只会交给本机 `yt-dlp` 使用，不会写入输出文件。
- 输出文件默认只保存清洗后的来源：URL 会移除 query string 和 fragment，本地文件只保存文件名。确实需要完整来源时，可以显式传入 `--include-source`。
- 生成稿、原始转写稿和 metadata 可能包含私密内容，请不要提交到公开仓库。
- 成本由你的 Google API key 承担，实际费用取决于视频时长、语速、音频密度和模型价格。

## 已知限制 / Roadmap

目前它还有很多不足，比如没有完整的 GUI，没有内置批量任务管理，字幕时间轴能力也还比较基础。后续可以继续改进 SRT/VTT 输出、字幕优先策略、批量处理、缓存、失败重试和更多模型后端。

## 安装

需要：

- Python 3.9+
- [`ffmpeg`](https://ffmpeg.org/)
- 一个 Google Gemini API key

克隆仓库：

```bash
git clone https://github.com/xisheng687/video-transcript-extractor.git
cd video-transcript-extractor
```

设置 API key：

```bash
export GOOGLE_API_KEY="your_google_api_key"  # pragma: allowlist secret
```

安装 Python 依赖：

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

如果你不想把 key 放进 shell 环境，也可以显式传入本地 `.env` 文件：

```bash
python3 scripts/extract_video_transcript.py "VIDEO_URL" \
  --env-file ./.env \
  --out-dir ./transcripts
```

每次运行会输出：

- `*-AI高质量校对稿.md`
- `*-transcript.txt`
- `*-raw-transcript.txt`
- `*-metadata.json`
- 中间音频文件，位于输出目录的 `_work/` 下

不要提交 `cookies.txt`、`.env`、API key，或包含隐私内容的生成稿。`.gitignore` 已覆盖默认输出目录和常见生成文件名，但如果你自定义输出位置，仍然需要自己确认。

## 给 AI Agent 使用

更简单的方式是直接把这个仓库链接发给 Codex CLI、Claude Code、Cursor Agent 或其他 AI Agent，然后说：

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
