# try:
#     with open("./data/gen.yaml", "w", encoding="utf-8") as f:
#         yaml.dump(template, f, allow_unicode=True, default_flow_style=False)
# except Exception as e:
#     logger.error(f"Error writing to gen.yaml: {e}")
if __name__ == "__main__":
    sub_list = [
        {
            "name": "狗狗加速",
            "url": "url1",
            "user_agent": "clash-verge/v2.4.3",
            "proxy": "http://127.0.0.1:7890",
            "rule_base_url": "https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release",
        },
        {
            "name": "Rancho",
            "url": "url2",
            "user_agent": "clash-verge/v2.4.3",
            "proxy": "http://127.0.0.1:7890",
            "rule_base_url": "https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release",
        },
    ]

    print([f"provider.{item['name']}" for item in sub_list])
    print([item["name"] for item in sub_list])

    print("12345/".rstrip("/"))
