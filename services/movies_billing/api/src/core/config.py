from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    postgres_dsn: PostgresDsn = 'postgresql+asyncpg://postgres:postgres@localhost:5432/subscriptions'
    project_name = 'Billing API'
    debug = True
    test = False
    stripe_secret_key: str

    jwt_secret_key: str = '123'
    jwt_algorithm: str = 'HS256'


settings = Settings()
