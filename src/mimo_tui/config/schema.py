from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EndpointConfig(BaseModel):
    url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    anthropic_url: str = "https://token-plan-cn.xiaomimimo.com/anthropic"
    api_key: str = ""
    timeout_s: int = 120


class ModelConfig(BaseModel):
    name: str = "MiMo-V2.5-Pro"
    reasoning: bool = True
    vision: bool = False
    audio_out: bool = False
    tools: bool = True
    max_tokens: int = 8192
    temperature: float = 0.6


class ApprovalConfig(BaseModel):
    policy: Literal["prompt", "allow_safe", "yolo"] = "prompt"
    auto_allow: list[str] = Field(default_factory=lambda: ["read_file", "glob", "grep"])


class SandboxConfig(BaseModel):
    project_root: str = "."
    shell_allowlist: list[str] = Field(
        default_factory=lambda: ["git", "ls", "cat", "rg", "python", "pytest", "npm", "node"]
    )
    shell_timeout_s: int = 60
    write_paths: list[str] = Field(default_factory=lambda: ["."])


class UIConfig(BaseModel):
    image_protocol: Literal["auto", "kitty", "iterm2", "sixel", "ascii"] = "auto"


class AudioConfig(BaseModel):
    auto_play: bool = True
    output_device: str = "default"
    save_dir: str = "~/.mimo-tui/audio/"


class MCPServer(BaseModel):
    name: str
    transport: Literal["stdio", "http"] = "stdio"
    command: str = ""
    args: list[str] = Field(default_factory=list)
    url: str = ""
    enabled: bool = True


class MCPConfig(BaseModel):
    servers: list[MCPServer] = Field(default_factory=list)


class ModelsCacheConfig(BaseModel):
    """Cache of models advertised by the configured endpoint.

    Populated automatically on app startup via ``GET /v1/models`` so that the
    UI does not have to depend on a hard-coded list of known model ids.
    """

    available: list[str] = Field(default_factory=list)
    synced_at: str = ""


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MIMO_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    language: Literal["en", "zh_CN"] = "en"
    theme: str = "tokyonight"
    mode: Literal["chat", "plan", "agent", "yolo"] = "agent"
    protocol: Literal["openai", "anthropic"] = "openai"

    endpoint: EndpointConfig = Field(default_factory=EndpointConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    approval: ApprovalConfig = Field(default_factory=ApprovalConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    models: ModelsCacheConfig = Field(default_factory=ModelsCacheConfig)

    @field_validator("endpoint", mode="before")
    @classmethod
    def inject_api_key_from_env(cls, v: object) -> object:
        import os
        if isinstance(v, dict) and not v.get("api_key"):
            v = dict(v)
            v["api_key"] = os.environ.get("MIMO_API_KEY", "")
        return v
