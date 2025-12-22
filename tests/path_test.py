from pathlib import Path

if __name__ == "__main__":
    dir = Path(".")
    print(str(dir / "baselines"))
    print(str(dir.parent.absolute() / "baselines"))
    print(str(dir.parent.parent.absolute() / "baselines"))
