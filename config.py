from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "GitHub Agent"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    LOG_LEVEL: str = "INFO"

    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""

    AWS_DEVOPS_WEBHOOK_URL: str = ""
    AWS_WEBHOOK_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()