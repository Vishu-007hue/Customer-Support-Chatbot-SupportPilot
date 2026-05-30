from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ai-support-chatbot"
    app_env: str = "dev"
    api_prefix: str = "/api"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "support_chatbot"

    nlp_provider: str = "local"  # local | dialogflow | rasa
    dialogflow_project_id: str = ""
    dialogflow_language_code: str = "en"
    dialogflow_credentials_path: str = ""

    rasa_endpoint: str = "http://localhost:5005/model/parse"

    confidence_threshold: float = 0.75
    low_confidence_threshold: float = 0.45
    response_cache_ttl_seconds: int = 120

    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"


settings = Settings()
