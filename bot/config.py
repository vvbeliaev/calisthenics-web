from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TELEGRAM_TOKEN: str
    ADMIN_ID: int
    WEBHOOK_BASE_URL: str = ""   # если пусто — polling режим
    PRODAMUS_SECRET: str
    DB_PATH: str = "subscribers.db"
    WELCOME_PHOTO: str = ""  # file_id или URL картинки для /start (пусто = без фото)
    TEST_MODE: bool = False  # если True — /start сразу выдаёт активную подписку (без оплаты)


settings = Settings()
