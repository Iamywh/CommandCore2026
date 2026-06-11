"""
Configuration and settings management for JARVIS2026.

Uses Pydantic v2 Settings for environment variable loading.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class OllamaSettings(BaseSettings):
    """Ollama LLM provider configuration."""

    base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    timeout: int = Field(default=120, alias="OLLAMA_TIMEOUT")
    director_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_DIRECTOR_MODEL")
    coder_model: str = Field(default="qwen2.5-coder:7b", alias="OLLAMA_CODER_MODEL")
    default_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_DEFAULT_MODEL")
    temperature: float = Field(default=0.7, alias="OLLAMA_TEMPERATURE")
    top_p: float = Field(default=0.9, alias="OLLAMA_TOP_P")
    top_k: int = Field(default=40, alias="OLLAMA_TOP_K")


class VoiceSettings(BaseSettings):
    """Speech-to-text and text-to-speech configuration."""

    enable_stt: bool = Field(default=False, alias="ENABLE_STT")
    enable_tts: bool = Field(default=False, alias="ENABLE_TTS")
    enable_wake_word: bool = Field(default=False, alias="ENABLE_WAKE_WORD")
    enable_clap_detection: bool = Field(default=False, alias="ENABLE_CLAP_DETECTION")

    stt_provider: str = Field(default="faster_whisper", alias="STT_PROVIDER")
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")

    tts_provider: str = Field(default="piper", alias="TTS_PROVIDER")
    piper_voice: str = Field(default="en_US-hfc_female-medium", alias="PIPER_VOICE")
    piper_speed: float = Field(default=1.0, alias="PIPER_SPEED")


class PathSettings(BaseSettings):
    """File system paths configuration."""

    workspace_root: Path = Field(default=Path("./workspace"), alias="WORKSPACE_ROOT")
    logs_dir: Path = Field(default=Path("./logs"), alias="LOGS_DIR")
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")

    memory_db_path: Path = Field(
        default=Path("./memory/db/jarvis_memory.sqlite3"), alias="MEMORY_DB_PATH"
    )
    journal_path: Path = Field(default=Path("./memory/journal"), alias="JOURNAL_PATH")
    journal_file: str = Field(default="daily_journal.md", alias="JOURNAL_FILE")

    audio_input_dir: Path = Field(
        default=Path("./data/audio/input"), alias="AUDIO_INPUT_DIR"
    )
    audio_output_dir: Path = Field(
        default=Path("./data/audio/output"), alias="AUDIO_OUTPUT_DIR"
    )

    def ensure_dirs(self) -> None:
        """Create necessary directories if they don't exist."""
        for path in [
            self.workspace_root,
            self.logs_dir,
            self.data_dir,
            self.memory_db_path.parent,
            self.journal_path,
            self.audio_input_dir,
            self.audio_output_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


class SecuritySettings(BaseSettings):
    """Security and permissions configuration."""

    max_tokens_per_request: int = Field(default=2048, alias="MAX_TOKENS_PER_REQUEST")
    require_approval_for_shell: bool = Field(
        default=True, alias="REQUIRE_APPROVAL_FOR_SHELL"
    )
    require_approval_for_git_commit: bool = Field(
        default=True, alias="REQUIRE_APPROVAL_FOR_GIT_COMMIT"
    )
    require_approval_for_file_delete: bool = Field(
        default=True, alias="REQUIRE_APPROVAL_FOR_FILE_DELETE"
    )
    allowed_workspace_paths: str = Field(
        default="./workspace,./data", alias="ALLOWED_WORKSPACE_PATHS"
    )

    def get_allowed_paths(self) -> list[str]:
        """Parse and return allowed workspace paths."""
        return [p.strip() for p in self.allowed_workspace_paths.split(",")]


class UISettings(BaseSettings):
    """User interface configuration."""

    width: int = Field(default=1200, alias="UI_WIDTH")
    height: int = Field(default=800, alias="UI_HEIGHT")
    theme: str = Field(default="dark", alias="UI_THEME")
    orb_animation_speed: float = Field(default=1.0, alias="ORB_ANIMATION_SPEED")


class AgentSettings(BaseSettings):
    """Agent configuration."""

    timeout: int = Field(default=60, alias="AGENT_TIMEOUT")
    retry_attempts: int = Field(default=3, alias="AGENT_RETRY_ATTEMPTS")

    route_dev_keywords: str = Field(
        default="code,dev,fix,debug,test,python,function,class,bug,refactor",
        alias="ROUTE_DEV_KEYWORDS",
    )
    route_cto_keywords: str = Field(
        default="architecture,design,performance,scalability,infrastructure",
        alias="ROUTE_CTO_KEYWORDS",
    )
    route_business_keywords: str = Field(
        default="priority,roadmap,business,plan,client,revenue",
        alias="ROUTE_BUSINESS_KEYWORDS",
    )
    route_notes_keywords: str = Field(
        default="save,journal,memory,log,record,note,remember",
        alias="ROUTE_NOTES_KEYWORDS",
    )

    def get_keywords_for_agent(self, agent_name: str) -> set[str]:
        """Get routing keywords for an agent."""
        if agent_name == "dev":
            return {k.strip() for k in self.route_dev_keywords.split(",")}
        elif agent_name == "cto":
            return {k.strip() for k in self.route_cto_keywords.split(",")}
        elif agent_name == "business":
            return {k.strip() for k in self.route_business_keywords.split(",")}
        elif agent_name == "notes":
            return {k.strip() for k in self.route_notes_keywords.split(",")}
        return set()


class IntegrationSettings(BaseSettings):
    """Optional integration configuration."""

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_repo: str | None = Field(default=None, alias="GITHUB_REPO")
    enable_browser_tools: bool = Field(default=False, alias="ENABLE_BROWSER_TOOLS")
    browser_headless: bool = Field(default=True, alias="BROWSER_HEADLESS")


class DebugSettings(BaseSettings):
    """Debug and development configuration."""

    debug: bool = Field(default=False, alias="DEBUG")
    show_prompts: bool = Field(default=False, alias="SHOW_PROMPTS")
    log_agent_decisions: bool = Field(default=True, alias="LOG_AGENT_DECISIONS")
    save_conversations: bool = Field(default=True, alias="SAVE_CONVERSATIONS")


class Settings(BaseSettings):
    """Main settings container combining all configuration sections."""

    app_name: str = Field(default="JARVIS2026", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ui: UISettings = Field(default_factory=UISettings)
    agents: AgentSettings = Field(default_factory=AgentSettings)
    integrations: IntegrationSettings = Field(default_factory=IntegrationSettings)
    debug: DebugSettings = Field(default_factory=DebugSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def initialize(self) -> None:
        """Initialize settings (create directories, etc)."""
        self.paths.ensure_dirs()


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.initialize()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global _settings
    _settings = Settings()
    _settings.initialize()
    return _settings
