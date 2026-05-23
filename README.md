# MiMo TUI

> **English** | [简体中文](#简体中文)

A feature-rich terminal UI for **Xiaomi MiMo** — the official MiMo platform.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg) ![License](https://img.shields.io/badge/license-Apache--2.0-green.svg) ![Status](https://img.shields.io/badge/status-alpha-orange.svg)

---

## Why MiMo TUI?

Compared to other MiMo terminal clients, MiMo TUI offers **five differentiators**:

1. **First-class reasoning-trace pane** — live `<think>` stream in a collapsible side panel, with per-turn token count and latency. Toggle with `Ctrl+R`.
2. **TTS audio playback in-terminal** — MiMo-V2.5-TTS variants play directly in your terminal via `sounddevice`. Audio cards in the chat with play/stop/save buttons.
3. **Dual-protocol client** — both the OpenAI-compatible `/v1` endpoint and the Anthropic-compatible `/anthropic` endpoint via the official Anthropic SDK. Hot-switch with `/protocol`.
4. **Multimodal input** — attach images for MiMo-V2-Omni with terminal-graphics preview (kitty / iTerm2 / sixel / ASCII fallback).
5. **Bilingual zh-CN / en UI** — hot-switch with `/lang` or `Ctrl+L`. UI strings localize; system prompts to the model stay in EN for fidelity.

Plus a **full agent loop** with plan / agent / yolo modes, per-tool approval, 8 builtin tools, and MCP server support.

---

## Quick Start

> **Note:** Not yet published to PyPI. Install from source for now.

```bash
# Clone and install from source
git clone https://github.com/orange90/mimo-tui
cd mimo-tui
pip install -e ".[audio]"        # include [audio] for TTS playback support

# Set your API key and launch
export MIMO_API_KEY=your_key_here
mimo
```

Or install directly from GitHub without cloning:

```bash
pip install "git+https://github.com/orange90/mimo-tui.git#egg=mimo-tui[audio]"
```

On first run, a setup wizard walks you through:
1. **API key** for `token-plan-cn.xiaomimimo.com` (or your self-hosted endpoint)
2. **Model selection** (with capability badges)
3. **Protocol** — OpenAI-compatible or Anthropic SDK
4. **Preferences** — language and theme

### Self-hosted MiMo

Point at any OpenAI-compatible endpoint (vLLM, SGLang, Ollama):

```bash
mimo --api-key sk-... --model MiMo-7B-RL
```

Or persist it in `~/.mimo-tui/config.toml`:

```toml
[endpoint]
url = "http://localhost:8000/v1"

[model]
name = "MiMo-7B-RL"
```

`mimo serve-detect` probes localhost for running engines on standard ports (Ollama 11434, vLLM 8000, SGLang 9001/30000).

---

## Requirements

- **Python 3.11+**
- Terminal with **256-color** support (best with truecolor)
- For TTS audio playback (optional): `portaudio` native library
  - Debian/Ubuntu: `apt install libportaudio2`
  - macOS: `brew install portaudio`
  - Then: `pip install "mimo-tui[audio]"`

---

## Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+M` | Open model picker |
| `Ctrl+R` | Toggle reasoning pane |
| `Ctrl+L` | Toggle language (en ↔ zh_CN) |
| `Ctrl+T` | Cycle theme |
| `Ctrl+N` | New session |
| `Ctrl+Q` | Quit |
| `Enter` | Send message |
| `Esc` | Close modal / cancel |

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/model <name>` | Switch model (or open picker without arg) |
| `/mode <chat\|plan\|agent\|yolo>` | Switch agent mode |
| `/protocol <openai\|anthropic>` | Switch wire protocol |
| `/lang <en\|zh_CN>` | Switch UI language |
| `/theme <name>` | Switch theme (tokyonight / catppuccin / mimo-light) |
| `/attach <path>` | Attach image for next message (multimodal models) |
| `/search <query>` | Full-text search across session history |
| `/tools` | List registered tools |
| `/mcp` | Show registered MCP tools |
| `/clear` | Clear current conversation |
| `/fork` | Fork session (copy current history into new session) |
| `/save` / `/load` | Save / load session |
| `/help` | Show command reference |

---

## Modes

| Mode | Description | Tool access |
|------|-------------|-------------|
| `chat` | Plain conversation | No tools |
| `plan` | Generate a step-by-step plan, no execution | Read-only |
| `agent` | Autonomous execution with **per-tool approval** | All tools, prompts on dangerous calls |
| `yolo` | Autonomous execution, no approvals | All tools, no prompts |

---

## Models

| Model | Reasoning | Vision | TTS | Tools |
|-------|-----------|--------|-----|-------|
| MiMo-V2.5-Pro | ✓ | | | ✓ |
| MiMo-V2.5 | ✓ | | | ✓ |
| MiMo-V2-Pro | ✓ | | | ✓ |
| MiMo-V2-Omni | ✓ | ✓ | ✓ | ✓ |
| MiMo-V2.5-TTS | | | ✓ | |
| MiMo-V2.5-TTS-VoiceClone | | | ✓ | |
| MiMo-V2.5-TTS-VoiceDesign | | | ✓ | |
| MiMo-V2-TTS | | | ✓ | |

---

## Builtin Tools

| Tool | Danger | Description |
|------|--------|-------------|
| `read_file` | safe | Read file contents with optional line offset/limit |
| `glob` | safe | Find files matching a glob pattern |
| `grep` | safe | Search a regex pattern in files (ripgrep if installed) |
| `web_fetch` | safe | Fetch a URL and return its text content |
| `todo_write` | safe | Manage a per-session TODO list |
| `write_file` | moderate | Create or overwrite a file (sandboxed paths) |
| `edit_file` | moderate | Replace an exact string in a file with diff preview |
| `shell_exec` | **dangerous** | Run a shell command (allowlist-gated, cwd-jailed, timeout) |

All paths and shell commands are restricted by `[sandbox]` config — see below.

---

## Configuration

Config is loaded and merged in this order (later overrides earlier):

1. Built-in defaults
2. `~/.mimo-tui/config.toml`
3. `.mimo/config.toml` (project-local)
4. `MIMO_*` environment variables
5. CLI flags

Example `~/.mimo-tui/config.toml`:

```toml
language = "en"                     # en | zh_CN
theme = "tokyonight"
mode = "agent"                      # chat | plan | agent | yolo
protocol = "openai"                 # openai | anthropic

[endpoint]
url = "https://token-plan-cn.xiaomimimo.com/v1"
anthropic_url = "https://token-plan-cn.xiaomimimo.com/anthropic"
api_key = "${env:MIMO_API_KEY}"
timeout_s = 120

[model]
name = "MiMo-V2.5-Pro"
max_tokens = 8192
temperature = 0.6

[approval]
policy = "prompt"                   # prompt | allow_safe | yolo
auto_allow = ["read_file", "glob", "grep"]

[sandbox]
project_root = "."
shell_allowlist = ["git", "ls", "cat", "rg", "python", "pytest", "npm", "node"]
shell_timeout_s = 60
write_paths = ["."]

[ui]
reasoning_pane = "visible"          # visible | collapsed | hidden
image_protocol = "auto"             # auto | kitty | iterm2 | sixel | ascii

[audio]
auto_play = true
save_dir = "~/.mimo-tui/audio/"

[[mcp.servers]]
name = "filesystem"
transport = "stdio"
command = "uvx"
args = ["mcp-server-filesystem", "."]
enabled = true
```

---

## CLI

```bash
mimo                              # launch the TUI
mimo --api-key sk-... --model MiMo-V2.5-Pro --mode agent
mimo doctor                       # check API connectivity, audio support, list models
mimo serve-detect                 # probe localhost for vLLM/SGLang/Ollama
```

---

## Development

```bash
git clone https://github.com/orange90/mimo-tui
cd mimo-tui
pip install -e ".[dev]"

pytest -q                         # 32 unit tests
ruff check src/                   # lint
mypy src/mimo_tui                 # type check
```

### Project layout

```
src/mimo_tui/
├── client/      # OpenAI + Anthropic streaming clients, SSE parser
├── agent/       # Async agent loop, modes, tool registry
├── tools/       # 8 builtin tools with sandbox
├── mcp/         # MCP server manager (stdio + http transports)
├── tui/         # Textual screens and widgets
├── audio/       # TTS playback via sounddevice
├── images/      # Multimodal pipeline + terminal-graphics adapters
├── sessions/    # SQLite store with FTS5 search
├── i18n/        # YAML locale catalogs (en, zh_CN)
├── providers/   # Capability table + local engine detection
└── config/      # Layered TOML config with pydantic schema
```

---

## License

Apache License 2.0 — see [LICENSE](./LICENSE).

---

<a id="简体中文"></a>

# MiMo TUI（简体中文）

> [English](#mimo-tui) | **简体中文**

为**小米 MiMo** 打造的功能丰富的终端 UI 客户端。

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg) ![License](https://img.shields.io/badge/license-Apache--2.0-green.svg) ![Status](https://img.shields.io/badge/status-alpha-orange.svg)

---

## 为什么选择 MiMo TUI？

相较于其他 MiMo 终端客户端，MiMo TUI 提供**五大特色**：

1. **一流的推理过程面板** — 在可折叠的侧边栏中实时显示 `<think>` 流，附带每轮 token 计数和延迟。按 `Ctrl+R` 切换。
2. **终端内 TTS 语音播放** — MiMo-V2.5-TTS 系列模型生成的语音通过 `sounddevice` 直接在终端中播放。对话中显示音频卡片，支持播放/停止/保存按钮。
3. **双协议客户端** — 同时支持 OpenAI 兼容 `/v1` 端点和官方 Anthropic SDK 通过 `/anthropic` 端点。`/protocol` 命令热切换。
4. **多模态输入** — 为 MiMo-V2-Omni 附加图片，终端图形预览（kitty / iTerm2 / sixel / ASCII 兜底）。
5. **中文/英文双语界面** — 通过 `/lang` 或 `Ctrl+L` 热切换。UI 字符串本地化；发送给模型的系统提示保持英文以确保保真度。

外加**完整的 Agent 循环**：plan / agent / yolo 三种模式、逐工具授权、8 个内置工具、MCP 服务器支持。

---

## 快速开始

> **提示：** 暂未发布到 PyPI，目前请从源码安装。

```bash
# 克隆并从源码安装
git clone https://github.com/orange90/mimo-tui
cd mimo-tui
pip install -e ".[audio]"        # 加 [audio] 以支持 TTS 语音播放

# 设置 API 密钥并启动
export MIMO_API_KEY=你的密钥
mimo
```

也可以不用 clone，直接从 GitHub 安装：

```bash
pip install "git+https://github.com/orange90/mimo-tui.git#egg=mimo-tui[audio]"
```

首次运行时，安装向导会引导你完成：
1. **API 密钥** — `token-plan-cn.xiaomimimo.com` 或自部署端点
2. **模型选择** — 含能力标签
3. **协议** — OpenAI 兼容 或 Anthropic SDK
4. **偏好设置** — 语言与主题

### 自部署 MiMo

指向任何 OpenAI 兼容端点（vLLM、SGLang、Ollama）：

```bash
mimo --api-key sk-... --model MiMo-7B-RL
```

或写入 `~/.mimo-tui/config.toml`：

```toml
[endpoint]
url = "http://localhost:8000/v1"

[model]
name = "MiMo-7B-RL"
```

`mimo serve-detect` 命令会探测本机标准端口上运行的推理引擎（Ollama 11434、vLLM 8000、SGLang 9001/30000）。

---

## 环境要求

- **Python 3.11+**
- 支持 **256 色**的终端（推荐 truecolor）
- TTS 音频播放（可选）：需要 `portaudio` 原生库
  - Debian/Ubuntu：`apt install libportaudio2`
  - macOS：`brew install portaudio`
  - 然后：`pip install "mimo-tui[audio]"`

---

## 快捷键

| 按键 | 操作 |
|------|------|
| `Ctrl+M` | 打开模型选择器 |
| `Ctrl+R` | 切换推理过程面板 |
| `Ctrl+L` | 切换语言（中文 ↔ 英文）|
| `Ctrl+T` | 切换主题 |
| `Ctrl+N` | 新建会话 |
| `Ctrl+Q` | 退出 |
| `Enter` | 发送消息 |
| `Esc` | 关闭弹窗 / 取消 |

---

## 斜杠命令

| 命令 | 说明 |
|------|------|
| `/model <名称>` | 切换模型（不带参数则打开选择器）|
| `/mode <chat\|plan\|agent\|yolo>` | 切换 Agent 模式 |
| `/protocol <openai\|anthropic>` | 切换通信协议 |
| `/lang <en\|zh_CN>` | 切换界面语言 |
| `/theme <名称>` | 切换主题（tokyonight / catppuccin / mimo-light）|
| `/attach <路径>` | 为下一条消息附加图片（多模态模型）|
| `/search <关键词>` | 在会话历史中全文搜索 |
| `/tools` | 列出已注册工具 |
| `/mcp` | 显示已注册的 MCP 工具 |
| `/clear` | 清空当前会话 |
| `/fork` | 复刻当前会话（复制历史到新会话）|
| `/save` / `/load` | 保存 / 加载会话 |
| `/help` | 显示命令帮助 |

---

## 模式

| 模式 | 说明 | 工具权限 |
|------|------|----------|
| `chat` | 纯对话 | 不使用工具 |
| `plan` | 生成步骤计划，不执行 | 仅只读 |
| `agent` | 自主执行，**逐工具授权** | 全部工具，危险操作弹窗确认 |
| `yolo` | 自主执行，无需授权 | 全部工具，无弹窗 |

---

## 支持的模型

| 模型 | 推理 | 视觉 | TTS | 工具 |
|------|------|------|-----|------|
| MiMo-V2.5-Pro | ✓ | | | ✓ |
| MiMo-V2.5 | ✓ | | | ✓ |
| MiMo-V2-Pro | ✓ | | | ✓ |
| MiMo-V2-Omni | ✓ | ✓ | ✓ | ✓ |
| MiMo-V2.5-TTS | | | ✓ | |
| MiMo-V2.5-TTS-VoiceClone | | | ✓ | |
| MiMo-V2.5-TTS-VoiceDesign | | | ✓ | |
| MiMo-V2-TTS | | | ✓ | |

---

## 内置工具

| 工具 | 危险等级 | 说明 |
|------|----------|------|
| `read_file` | 安全 | 读取文件内容，可选行偏移/限制 |
| `glob` | 安全 | 按 glob 模式查找文件 |
| `grep` | 安全 | 在文件中搜索正则（如安装则使用 ripgrep）|
| `web_fetch` | 安全 | 抓取 URL 并返回文本内容 |
| `todo_write` | 安全 | 管理当前会话的 TODO 列表 |
| `write_file` | 中等 | 创建或覆盖文件（沙盒路径限制）|
| `edit_file` | 中等 | 替换文件中指定字符串，显示 diff |
| `shell_exec` | **危险** | 运行 shell 命令（允许列表、cwd 沙盒、超时）|

所有路径和 shell 命令受 `[sandbox]` 配置约束 — 见下文。

---

## 配置

配置按以下顺序加载并合并（后者覆盖前者）：

1. 内置默认值
2. `~/.mimo-tui/config.toml`
3. `.mimo/config.toml`（项目级）
4. `MIMO_*` 环境变量
5. CLI 参数

`~/.mimo-tui/config.toml` 示例：

```toml
language = "zh_CN"                  # en | zh_CN
theme = "tokyonight"
mode = "agent"                      # chat | plan | agent | yolo
protocol = "openai"                 # openai | anthropic

[endpoint]
url = "https://token-plan-cn.xiaomimimo.com/v1"
anthropic_url = "https://token-plan-cn.xiaomimimo.com/anthropic"
api_key = "${env:MIMO_API_KEY}"
timeout_s = 120

[model]
name = "MiMo-V2.5-Pro"
max_tokens = 8192
temperature = 0.6

[approval]
policy = "prompt"                   # prompt | allow_safe | yolo
auto_allow = ["read_file", "glob", "grep"]

[sandbox]
project_root = "."
shell_allowlist = ["git", "ls", "cat", "rg", "python", "pytest", "npm", "node"]
shell_timeout_s = 60
write_paths = ["."]

[ui]
reasoning_pane = "visible"          # visible | collapsed | hidden
image_protocol = "auto"             # auto | kitty | iterm2 | sixel | ascii

[audio]
auto_play = true
save_dir = "~/.mimo-tui/audio/"

[[mcp.servers]]
name = "filesystem"
transport = "stdio"
command = "uvx"
args = ["mcp-server-filesystem", "."]
enabled = true
```

---

## 命令行

```bash
mimo                              # 启动 TUI
mimo --api-key sk-... --model MiMo-V2.5-Pro --mode agent
mimo doctor                       # 检查 API 连接、音频支持、列出可用模型
mimo serve-detect                 # 探测本机 vLLM/SGLang/Ollama
```

---

## 开发

```bash
git clone https://github.com/orange90/mimo-tui
cd mimo-tui
pip install -e ".[dev]"

pytest -q                         # 32 个单元测试
ruff check src/                   # 代码检查
mypy src/mimo_tui                 # 类型检查
```

### 项目结构

```
src/mimo_tui/
├── client/      # OpenAI + Anthropic 流式客户端，SSE 解析
├── agent/       # 异步 Agent 循环、模式、工具注册表
├── tools/       # 8 个带沙盒的内置工具
├── mcp/         # MCP 服务器管理（stdio + http 传输）
├── tui/         # Textual 屏幕与组件
├── audio/       # 通过 sounddevice 播放 TTS
├── images/      # 多模态流水线 + 终端图形适配
├── sessions/    # 基于 SQLite + FTS5 的会话存储
├── i18n/        # YAML 多语言目录（en、zh_CN）
├── providers/   # 能力表 + 本机引擎探测
└── config/      # 基于 pydantic 的分层 TOML 配置
```

---

## 协议

Apache License 2.0 — 详见 [LICENSE](./LICENSE)。
