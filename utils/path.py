# 为文件路径添加后缀
from pathlib import Path


def gen_fp_with_suffix(fp: str, suffix: str):
    path_obj = Path(fp)

    directory = path_obj.parent  # 目录
    # filename = path_obj.name  # 文件名,包含后缀
    file_stem = path_obj.stem  # 文件名,不含后缀
    file_suffix = path_obj.suffix  # ".csv"

    new_path = directory / f"{file_stem}_{suffix}{file_suffix}"
    return new_path


if __name__ == "__main__":
    gen_fp_with_suffix("d:/github/meme2046/data/bitget_sf_0.csv", "tmp")
