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
