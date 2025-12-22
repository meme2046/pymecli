import importlib.metadata
from importlib import resources

import toml

if __name__ == "__main__":
    metadata = importlib.metadata.metadata("pymecli")
    print(metadata["Name"])
    print(metadata["Summary"])
    print(metadata["Version"])

    with (
        resources.files("pymecli")
        .joinpath("pyproject.toml")
        .open("r", encoding="utf-8") as f
    ):
        project = toml.load(f)["project"]
        print(project["version"])
