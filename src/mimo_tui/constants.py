from pathlib import Path

APP_NAME = "mimo-tui"
APP_DIR = Path.home() / ".mimo-tui"
CONFIG_FILE = APP_DIR / "config.toml"
SESSIONS_DB = APP_DIR / "sessions.db"
AUDIO_DIR = APP_DIR / "audio"
LOG_FILE = APP_DIR / "mimo.log"

OFFICIAL_API_URL = "https://token-plan-cn.xiaomimimo.com/v1"
OFFICIAL_ANTHROPIC_URL = "https://token-plan-cn.xiaomimimo.com/anthropic"

AGENT_MAX_ITERATIONS = 25
STREAM_FLUSH_MS = 30

# Trigger ratio for automatic context compaction (token usage / context window).
# Claude Code uses ~0.83 by default; we land slightly below at 0.80 for safety.
AUTO_COMPACT_THRESHOLD = 0.80
# Cap output tokens for the summary stream so it cannot itself overflow.
AUTO_COMPACT_MAX_OUTPUT = 4096
COMPACT_RECAP_HEADER = "[Compacted conversation summary]\n"
COMPACT_ACK = "Got it — I have the recap and will continue from here."
