from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str
    cosmos_endpoint: str
    cosmos_key: str
    sql_connection_string: str
    storage_connection_string: str
    appinsights_connection_string: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
