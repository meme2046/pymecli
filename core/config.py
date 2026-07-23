import importlib.metadata

from pydantic_settings import BaseSettings

metadata = importlib.metadata.metadata("pymecli")
# module_dir = Path(__file__).resolve().parent.parent

# project = read_toml(str(module_dir / "./pyproject.toml"))["project"]


class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = metadata["Name"]

    REDIS_HOST: str = "192.168.123.7"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    PROJECT_DESCRIPTION: str = (
        f"{metadata['Summary']}, FastAPI提供: clash订阅转换、redis API"
    )
    PROJECT_VERSION: str = metadata["Version"]

    class Config:
        env_prefix = "PYME_CLI_"  # 添加环境变量前缀
        case_sensitive = True

    def reload(self):
        new_settings = Settings()
        for field in Settings.model_fields:
            setattr(self, field, getattr(new_settings, field))


settings = Settings()

print(f"project: {settings.PROJECT_NAME}")
print(f"version: {settings.PROJECT_VERSION}")
print(f"description: {settings.PROJECT_DESCRIPTION}")
