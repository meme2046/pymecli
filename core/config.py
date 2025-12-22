from pydantic_settings import BaseSettings

from utils.toml import read_toml

project = read_toml("./pyproject.toml")["project"]


class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api/v1"
    NAME: str = project["name"]
    DESCRIPTION: str = f"{project['description']},"
    "FastAPI提供[onnx-paddleocr识别、douzero、clash订阅转换]"
    VERSION: str = project["version"]

    class Config:
        env_prefix = "MY_CLI_API_"  # 添加环境变量前缀
        case_sensitive = True

    def reload(self):
        new_settings = Settings()
        for field in Settings.model_fields:
            setattr(self, field, getattr(new_settings, field))


settings = Settings()
