from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TELEGRAM_TOKEN: str
    ADMIN_ID: int
    WEBHOOK_BASE_URL: str = ""  # если пусто — polling режим
    PRODAMUS_SECRET: str
    PRODAMUS_URL: str = ""  # базовый payform URL для разовых платежей (личное занятие, благодарность)
    DB_PATH: str = "subscribers.db"
    TEST_MODE: bool = False
    ADMIN_PASSWORD: str = ""  # пусто — веб-админка отключена


settings = Settings()  # type: ignore[call-arg]
