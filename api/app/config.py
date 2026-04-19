from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    plaid_client_id: str = ""
    plaid_secret_sandbox: str = ""
    plaid_env: str = "sandbox"
    plaid_products: str = "transactions,auth"
    plaid_country_codes: str = "US"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-7-sonnet-20250219"

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Cloud SQL portfolio-pg / aifp database. See api/README.md and scripts/db-proxy.sh.
    database_url: str = ""

    @property
    def plaid_configured(self) -> bool:
        return bool(self.plaid_client_id and self.plaid_secret_sandbox)

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
