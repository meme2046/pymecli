import importlib.metadata

metadata = importlib.metadata.metadata("pymecli")
# module_dir = Path(__file__).resolve().parent.parent

# project = read_toml(str(module_dir / "./pyproject.toml"))["project"]


class Settings:
    # API配置
    API_V1_STR: str = "/api/v1"
    NAME: str = metadata["Name"]
    DESCRIPTION: str = (
        f"{metadata['Summary']}, FastAPI提供: clash订阅转换、baidu.gushitong api"
    )
    VERSION: str = metadata["Version"]

    print(f"project: {NAME}")
    print(f"version: {VERSION}")
    print(f"description: {DESCRIPTION}")


settings = Settings()
