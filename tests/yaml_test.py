import time

import yaml


def read_yaml(fp_path):
    with open(fp_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        print(data)
        return data


if __name__ == "__main__":
    print(time.time())
