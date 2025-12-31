import json

if __name__ == "__main__":
    data: None | str = '{"name": "John", "age": 30}'
    data = "[]"
    json_data = json.loads(data)
    print(json_data)
