import os

import requests
import typer
import uvicorn
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response

from utils.logger import get_logger

load_dotenv("d:/.env")
logger = get_logger(__name__)
cli = typer.Typer()
app = FastAPI()


def get_clash_yaml(sub_list: list[dict]):
    proxies = None
    if request_proxy:
        proxies = {
            "http": request_proxy,
            "https": request_proxy,
        }

    with open("./data/template.yaml", "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    template["proxy-groups"].extend(
        [
            {
                "name": "全局选择",
                "type": "select",
                "proxies": ["自动选择", "手动选择", "轮询"]
                + [item["name"] for item in sub_list],
            },
            {
                "name": "自动选择",
                "type": "url-test",
                "url": "https://www.gstatic.com/generate_204",
                "interval": 300,
                "tolerance": 11,
                "lazy": True,
                "use": [f"provider.{item['name']}" for item in sub_list],
            },
            {
                "name": "手动选择",
                "type": "select",
                "use": [f"provider.{item['name']}" for item in sub_list],
            },
            {
                "name": "轮询",
                "type": "load-balance",
                "url": "https://www.gstatic.com/generate_204",
                "interval": 300,
                "lazy": True,
                "strategy": "round-robin",
                "use": [f"provider.{item['name']}" for item in sub_list],
            },
        ]
    )
    userinfo = ""
    for item in sub_list:
        headers = {"User-Agent": item["user_agent"]} if item["user_agent"] else {}

        if not item["url"]:
            raise ValueError("Invalid subscription URL.")
        response = requests.get(item["url"], headers=headers, proxies=proxies)
        response.raise_for_status()
        if not userinfo:
            userinfo = response.headers["Subscription-Userinfo"]
        remote_config = yaml.safe_load(response.text)

        ps = remote_config.get("proxies", [])
        if not ps:
            raise ValueError("No proxies found in subscription.")

        template["proxy-providers"][f"provider.{item['name']}"] = {
            "type": "inline",
            "payload": ps,
        }

        template["proxy-groups"].append(
            {
                "name": item["name"],
                "type": "url-test",
                "url": "https://www.gstatic.com/generate_204",
                "interval": 300,
                "tolerance": 11,
                "lazy": True,
                "use": [f"provider.{item['name']}"],
            },
        )

    # 获取rules
    rule_list = [
        [f"{my_rule_base_url}/direct.yaml", "DIRECT"],
        [f"{my_rule_base_url}/proxy.yaml", "全局选择"],
        [
            f"{my_rule_base_url}/round.yaml",
            "轮询",
        ],
    ]

    for item in rule_list:
        response = requests.get(item[0], proxies=proxies)
        response.raise_for_status()
        remote = yaml.safe_load(response.text)
        template["rule-providers"][os.path.basename(item[0])] = {
            "type": "inline",
            "behavior": "classical",
            "payload": remote["payload"],
        }

        template["rules"].append(f"RULE-SET,{os.path.basename(item[0])},{item[1]}")

    template["rule-providers"].update(
        {
            "applications": {
                "type": "http",
                "behavior": "classical",
                "url": f"{rule_base_url}/applications.txt",
                "path": "./ruleset/applications.yaml",
                "interval": 86400,
            },
            "private": {
                "type": "http",
                "behavior": "domain",
                "url": f"{rule_base_url}/private.txt",
                "path": "./ruleset/private.yaml",
                "interval": 86400,
            },
            "icloud": {
                "type": "http",
                "behavior": "domain",
                "url": f"{rule_base_url}/icloud.txt",
                "path": "./ruleset/icloud.yaml",
                "interval": 86400,
            },
            "apple": {
                "type": "http",
                "behavior": "domain",
                "url": f"{rule_base_url}/apple.txt",
                "path": "./ruleset/apple.yaml",
                "interval": 86400,
            },
            "google": {
                "type": "http",
                "behavior": "domain",
                "url": f"{rule_base_url}/google.txt",
                "path": "./ruleset/google.yaml",
                "interval": 86400,
            },
            "proxy": {
                "type": "http",
                "behavior": "domain",
                "url": f"{rule_base_url}/proxy.txt",
                "path": "./ruleset/proxy.yaml",
                "interval": 86400,
            },
            "direct": {
                "type": "http",
                "behavior": "domain",
                "url": f"{rule_base_url}/direct.txt",
                "path": "./ruleset/direct.yaml",
                "interval": 86400,
            },
            "lancidr": {
                "type": "http",
                "behavior": "ipcidr",
                "url": f"{rule_base_url}/lancidr.txt",
                "path": "./ruleset/lancidr.yaml",
                "interval": 86400,
            },
            "cncidr": {
                "type": "http",
                "behavior": "ipcidr",
                "url": f"{rule_base_url}/cncidr.txt",
                "path": "./ruleset/cncidr.yaml",
                "interval": 86400,
            },
            "telegramcidr": {
                "type": "http",
                "behavior": "ipcidr",
                "url": f"{rule_base_url}/telegramcidr.txt",
                "path": "./ruleset/telegramcidr.yaml",
                "interval": 86400,
            },
        },
    )

    template["rules"].extend(
        [
            "RULE-SET,applications,DIRECT",
            "DOMAIN,clash.razord.top,DIRECT",
            "DOMAIN,yacd.haishan.me,DIRECT",
            "RULE-SET,private,DIRECT",
            "RULE-SET,icloud,DIRECT",
            "RULE-SET,apple,DIRECT",
            "RULE-SET,google,全局选择",
            "RULE-SET,proxy,全局选择",
            "RULE-SET,direct,DIRECT",
            "RULE-SET,lancidr,DIRECT",
            "RULE-SET,cncidr,DIRECT",
            "RULE-SET,telegramcidr,全局选择",
            "GEOIP,LAN,DIRECT,no-resolve",
            "GEOIP,CN,DIRECT,no-resolve",
            "MATCH,全局选择",
        ]
    )

    return template, userinfo


def str2json(urls: str, agents: str, names: str):
    url_list = urls.split(",") if urls else []
    agents_list = agents.split(",") if agents else []
    name_list = names.split(",") if names else []

    max_length = max(len(url_list), len(agents_list), len(name_list))

    while len(url_list) < max_length:
        url_list.append("")
    while len(agents_list) < max_length:
        agents_list.append("")
    while len(name_list) < max_length:
        name_list.append("")

    sub_list = []

    for i in range(max_length):
        if not url_list[i]:
            raise ValueError(f"Invalid subscription URL. #{i + 1}")

        sub_list.append(
            {
                "url": url_list[i],
                "user_agent": agents_list[i] if agents_list[i] else "",
                "name": name_list[i] if name_list[i] else f"订阅{i}",
            }
        )

    return sub_list


@app.get("/clash")
async def clash(
    urls: str = Query(..., description="订阅URL,逗号分隔"),
    agents: str = Query(
        "clash-verge/v2.4.3",
        description="User-Agent,逗号分隔(根据客户段选择)",
    ),
    names: str = Query(
        "订阅1", description="订阅名称,逗号分隔(可选,在客户端中的显示名)"
    ),
):
    try:
        # 将JSON字符串解析为Python对象
        sub_list = str2json(urls, agents, names)
        yaml_content, userinfo = get_clash_yaml(sub_list)
        yaml_string = yaml.dump(
            yaml_content, allow_unicode=True, default_flow_style=False
        )
        return Response(
            headers={"Subscription-Userinfo": userinfo},
            content=yaml_string,
            media_type="text/yaml",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@cli.command()
def run_app(
    host: str = "0.0.0.0",
    port: int = 7777,
    ssl_keyfile: str = typer.Option(
        None,
        "--ssl-keyfile",
        "-sk",
        help="ssl keyfile",
    ),
    ssl_certfile: str = typer.Option(
        None,
        "--ssl-certfile",
        "-sc",
        help="ssl certfile",
    ),
    rule: str = typer.Option(
        "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release",
        "--rule",
        "-r",
        help="Rule base URL",
    ),
    my_rule: str = typer.Option(
        "https://raw.githubusercontent.com/meme2046/data/refs/heads/main/clash",
        "--my_rule",
        "-mr",
        help="我的自定义Rule base URL",
    ),
    proxy: str = typer.Option(
        None,
        "--proxy",
        "-p",
        help="服务器代理,传入则通过代理请求订阅",
    ),
):
    global rule_base_url, my_rule_base_url, request_proxy
    rule_base_url = rule.rstrip("/")
    my_rule_base_url = my_rule.rstrip("/")
    request_proxy = proxy.rstrip("/")

    uvicorn.run(
        "mecli.clash:app",
        host=host,
        port=port,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
