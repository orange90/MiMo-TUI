# MiMo TUI

A feature-rich terminal UI for **Xiaomi MiMo** — the official MiMo platform.

> **Differentiators vs existing MiMo TUIs:**
> - First-class **reasoning-trace pane** — live `<think>` stream in a collapsible side panel with token count + latency
> - **TTS audio playback** in-terminal (MiMo-V2.5-TTS variants) via `sounddevice` — play/stop/save buttons in chat
> - **Dual-protocol client** — OpenAI-compatible `/v1` and Anthropic SDK `/anthropic` with hot-switch
> - **Multimodal** — MiMo-V2-Omni image attach + terminal-graphics preview (kitty/iTerm2/sixel/ASCII)
> - **Bilingual zh-CN/en** UI with hot-switch (`/lang zh_CN`)
> - Full **agent loop + MCP** — plan/agent/yolo modes, per-tool approval, 8 builtin tools

---

## Quick Start

```bash
pip install mimo-tui          # or: pip install "mimo-tui[audio]" for TTS playback
export MIMO_API_KEY=your_key
mimo
```

First run opens the **setup wizard**: API key → model → protocol → language/theme.

### Self-hosted

Point to any OpenAI-compatible endpoint (vLLM, SGLang, Ollama):

```bash
mimo --api-key sk-... --model MiMo-7B-RL
# or in ~/.mimo-tui/config.toml:
# [endpoint]
# url = "http://localhost:8000/v1"
```

---

## Requirements

- Python 3.11+
- Terminal with 256-color support
- `portaudio` native library for TTS audio (optional): `apt install libportaudio2` / `brew install portaudio`

---

## Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+M` | Model picker |
| `Ctrl+R` | Toggle reasoning pane |
| `Ctrl+L` | Toggle language (en ↔ zh_CN) |
| `Ctrl+T` | Cycle theme |
| `Ctrl+N` | New session |
| `Ctrl+Q` | Quit |

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/model <name>` | Switch model |
| `/mode <chat\|plan\|agent\|yolo>` | Switch mode |
| `/protocol <openai\|anthropic>` | Switch protocol |
| `/lang <en\|zh_CN>` | Switch language |
| `/theme <name>` | Switch theme |
| `/attach <path>` | Attach image (multimodal) |
| `/search <query>` | Full-text search sessions |
| `/tools` | List available tools |
| `/mcp` | Show registered MCP tools |
| `/clear` | Clear conversation |
| `/fork` | Fork session |
| `/help` | Show all commands |

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

## Configuration

Config is loaded from (in order, merged):
1. Built-in defaults
2. `~/.mimo-tui/config.toml`
3. `.mimo/config.toml` (project-local)
4. `MIMO_*` env vars
5. CLI flags

Example `~/.mimo-tui/config.toml`:

```toml
language = "en"
theme = "tokyonight"
mode = "agent"
protocol = "openai"

[endpoint]
url = "https://token-plan-cn.xiaomimimo.com/v1"
api_key = "your-api-key"

[model]
name = "MiMo-V2.5-Pro"
max_tokens = 8192

[audio]
auto_play = true

[[mcp.servers]]
name = "filesystem"
transport = "stdio"
command = "uvx"
args = ["mcp-server-filesystem", "."]
enabled = true
```

---

## Development

```bash
git clone ...
pip install -e ".[dev]"
pytest -q           # run tests
ruff check src/     # lint
mypy src/mimo_tui   # type check
```

---

## 简体中文

MiMo TUI 是小米 MiMo 的功能丰富终端 UI 客户端，支持：

- **推理过程面板** — 实时显示 `<think>` 流，带 token 统计
- **TTS 语音合成** — 在终端中播放 MiMo 语音（需安装 `portaudio`）
- **双协议客户端** — OpenAI 兼容 `/v1` 与 Anthropic SDK `/anthropic` 热切换
- **多模态输入** — 图片附件 + 终端预览（kitty/iTerm2/sixel）
- **双语界面** — 中文/英文热切换（`/lang zh_CN`）
- **完整 Agent 循环** — plan/agent/yolo 模式，工具授权，MCP 扩展

```bash
pip install mimo-tui
export MIMO_API_KEY=你的密钥
mimo
```

---

## License

Apache 2.0
