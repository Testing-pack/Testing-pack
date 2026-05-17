from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MAIN_SERVICE_URL: str = "http://localhost:8000"

    SPLIT_DB_HOST: str = "localhost"
    SPLIT_DB_PORT: int = 5433
    SPLIT_DB_NAME: str = "split_db"
    SPLIT_DB_USER: str = "split_user"
    SPLIT_DB_PASS: str = "split_pass"

    @property
    def SPLIT_DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.SPLIT_DB_USER}:{self.SPLIT_DB_PASS}"
            f"@{self.SPLIT_DB_HOST}:{self.SPLIT_DB_PORT}/{self.SPLIT_DB_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()