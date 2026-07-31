import os
from pathlib import Path

import requests
import yaml
from fastapi import Depends

module_dir = Path(__file__).resolve().parent.parent

TEMPLATE_URL = "https://raw.githubusercontent.com/meme2046/data/main/clash/template.yaml"

# 白名单模式最终规则
WHITELIST_RULES = [
    "RULE-SET,applications,DIRECT",
    "RULE-SET,private,DIRECT",
    "RULE-SET,icloud,DIRECT",
    "RULE-SET,apple,DIRECT",
    "RULE-SET,google,全局选择",
    "RULE-SET,proxy,全局选择",
    "RULE-SET,direct,DIRECT",
    "RULE-SET,lancidr,DIRECT",
    "RULE-SET,cncidr,DIRECT",
    "RULE-SET,telegramcidr,全局选择",
    "GEOIP,LAN,DIRECT",
    "GEOIP,CN,DIRECT",
    "MATCH,全局选择",
]

# 黑名单模式最终规则
BLACKLIST_RULES = [
    "RULE-SET,applications,DIRECT",
    "RULE-SET,private,DIRECT",
    "RULE-SET,tld-not-cn,全局选择",
    "RULE-SET,gfw,全局选择",
    "RULE-SET,telegramcidr,全局选择",
    "MATCH,DIRECT",
]


class ClashConfig:
    def __init__(self, rule_base_url: str, my_rule_base_url: str, request_proxy: str):
        self.rule_base_url = rule_base_url.rstrip("/")
        self.my_rule_base_url = my_rule_base_url.rstrip("/")
        self.request_proxy = request_proxy


class ClashYamlGenerator:
    def __init__(self, config: ClashConfig):
        self.rule_base_url = config.rule_base_url
        self.my_rule_base_url = config.my_rule_base_url
        self.request_proxy = config.request_proxy

    # ---------- 通用 helpers ----------

    def _get_proxies(self):
        if not self.request_proxy:
            return None
        return {"http": self.request_proxy, "https": self.request_proxy}

    def _load_template(self, proxies=None):
        """从远程获取 template.yaml,失败时回退到本地文件"""
        try:
            response = requests.get(TEMPLATE_URL, proxies=proxies)
            response.raise_for_status()
            template = yaml.safe_load(response.text)
            if template:
                return template
        except Exception:
            pass
        with open(str(module_dir / "data/template.yaml"), "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _fetch_subscriptions(self, sub_list, proxies):
        """抓取并校验所有订阅,返回 [(item, ps), ...] 和 userinfo"""
        userinfo = ""
        results = []
        for item in sub_list:
            headers = {"User-Agent": item["user_agent"]} if item["user_agent"] else {}

            if not item["url"]:
                raise ValueError("Invalid subscription URL.")
            response = requests.get(item["url"], headers=headers, proxies=proxies)
            response.raise_for_status()
            if not userinfo:
                userinfo = response.headers["Subscription-Userinfo"]
            remote_config = yaml.safe_load(response.text)

            # 检查 remote_config 是否为 None
            if remote_config is None:
                raise ValueError("Invalid subscription content: empty or invalid YAML.")

            ps = remote_config.get("proxies", [])
            if not ps:
                raise ValueError("No proxies found in subscription.")

            results.append((item, ps))
        return results, userinfo

    def _add_inline_rule_providers(self, template, proxies):
        """从 my_rule_base_url 拉取 inline 规则集并写入 template"""
        rule_list = [
            [f"{self.my_rule_base_url}/direct.yaml", "DIRECT"],
            [f"{self.my_rule_base_url}/proxy.yaml", "全局选择"],
            [f"{self.my_rule_base_url}/round.yaml", "轮询"],
            [f"{self.my_rule_base_url}/reject.yaml", "REJECT"],
        ]
        for url, target in rule_list:
            response = requests.get(url, proxies=proxies)
            response.raise_for_status()
            remote = yaml.safe_load(response.text)
            name = os.path.basename(url)
            template["rule-providers"][name] = {
                "type": "inline",
                "behavior": "classical",
                "payload": remote["payload"],
            }
            template["rules"].append(f"RULE-SET,{name},{target}")

    def _http_rule_provider(self, name, behavior):
        """生成单个 http 类型 rule-provider"""
        return {
            "type": "http",
            "format": "yaml",
            "behavior": behavior,
            "url": f"{self.rule_base_url}/{name}.txt",
            "path": f"./ruleset/{name}.yaml",
            "interval": 86400,
        }

    def _whitelist_http_rule_providers(self):
        return {
            "applications": self._http_rule_provider("applications", "classical"),
            "private": self._http_rule_provider("private", "domain"),
            "icloud": self._http_rule_provider("icloud", "domain"),
            "apple": self._http_rule_provider("apple", "domain"),
            "google": self._http_rule_provider("google", "domain"),
            "proxy": self._http_rule_provider("proxy", "domain"),
            "direct": self._http_rule_provider("direct", "domain"),
            "lancidr": self._http_rule_provider("lancidr", "ipcidr"),
            "cncidr": self._http_rule_provider("cncidr", "ipcidr"),
            "telegramcidr": self._http_rule_provider("telegramcidr", "ipcidr"),
        }

    def _blacklist_http_rule_providers(self):
        return {
            "applications": self._http_rule_provider("applications", "classical"),
            "private": self._http_rule_provider("private", "domain"),
            "tld-not-cn": self._http_rule_provider("tld-not-cn", "domain"),
            "telegramcidr": self._http_rule_provider("telegramcidr", "ipcidr"),
            "gfw": self._http_rule_provider("gfw", "domain"),
        }

    def _provider_proxy_groups(self, sub_list):
        """provider 风格的 proxy-groups(genPW / genPB)"""
        use_list = [f"provider.{item['name']}" for item in sub_list]
        return [
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
                "use": use_list,
            },
            {
                "name": "手动选择",
                "type": "select",
                "use": use_list,
            },
            {
                "name": "轮询",
                "type": "load-balance",
                "url": "https://api.bitget.com/api/v2/public/time",
                "interval": 300,
                "lazy": True,
                "strategy": "round-robin",
                "use": use_list,
            },
        ]

    def _inline_proxy_groups(self, sub_list):
        """include-all 风格的 proxy-groups(genB)"""
        return [
            {
                "name": "全局选择",
                "type": "select",
                "proxies": ["自动选择", "手动选择", "轮询"]
                + [item["name"] for item in sub_list],
            },
            {"name": "自动选择", "type": "url-test", "include-all": True},
            {"name": "手动选择", "type": "select", "include-all": True},
            {
                "name": "轮询",
                "type": "load-balance",
                "url": "https://api.bitget.com/api/v2/public/time",
                "strategy": "round-robin",
                "include-all": True,
            },
        ]

    def _add_provider_sub(self, template, item, ps):
        """单个订阅写入 proxy-providers + url-test group(genPW / genPB)"""
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
            }
        )

    def _add_inline_sub(self, template, item, ps):
        """单个订阅直接写入 proxies + url-test group(genB)"""
        template["proxies"].extend(ps)
        template["proxy-groups"].append(
            {
                "name": item["name"],
                "type": "url-test",
                "proxies": [p["name"] for p in ps],
            }
        )

    def _add_base_rules(self, template, with_dst_port=False):
        """IP-CIDR / DOMAIN 基础规则(genPB / genB),genB 含饥荒端口"""
        template["rules"].extend(
            [
                "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve",
                "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
                "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve",
                "IP-CIDR,127.0.0.0/8,DIRECT,no-resolve",
            ]
        )
        if with_dst_port:
            template["rules"].extend(
                [
                    "DST-PORT,10999,DIRECT",
                    "DST-PORT,10998,DIRECT",
                    "DST-PORT,27016,DIRECT",
                    "DST-PORT,27017,DIRECT",
                    "DST-PORT,8766,DIRECT",
                    "DST-PORT,8767,DIRECT",
                ]
            )
        template["rules"].extend(
            [
                "DOMAIN,clash.razord.top,DIRECT",
                "DOMAIN,yacd.haishan.me,DIRECT",
                # "DOMAIN,accounts.klei.com,全局选择",
            ]
        )

    # ---------- 三种生成模式 ----------

    # 白名单模式 Rules 配置方式
    def genPW(self, sub_list: list[dict]):
        proxies = self._get_proxies()
        template = self._load_template(proxies)

        template["proxy-groups"].extend(self._provider_proxy_groups(sub_list))

        subs, userinfo = self._fetch_subscriptions(sub_list, proxies)
        for item, ps in subs:
            self._add_provider_sub(template, item, ps)

        self._add_inline_rule_providers(template, proxies)
        template["rule-providers"].update(self._whitelist_http_rule_providers())
        template["rules"].extend(WHITELIST_RULES)

        return template, userinfo

    # 黑名单模式 Rules 配置方式
    def genPB(self, sub_list: list[dict]):
        proxies = self._get_proxies()
        template = self._load_template(proxies)

        template["proxy-groups"].extend(self._provider_proxy_groups(sub_list))

        subs, userinfo = self._fetch_subscriptions(sub_list, proxies)
        for item, ps in subs:
            self._add_provider_sub(template, item, ps)

        self._add_base_rules(template, with_dst_port=False)
        self._add_inline_rule_providers(template, proxies)
        template["rule-providers"].update(self._blacklist_http_rule_providers())
        template["rules"].extend(BLACKLIST_RULES)

        return template, userinfo

    def genB(self, sub_list: list[dict]):
        proxies = self._get_proxies()
        template = self._load_template(proxies)

        template["proxy-groups"].extend(self._inline_proxy_groups(sub_list))

        template["proxies"] = []
        subs, userinfo = self._fetch_subscriptions(sub_list, proxies)
        for item, ps in subs:
            self._add_inline_sub(template, item, ps)

        self._add_base_rules(template, with_dst_port=True)
        self._add_inline_rule_providers(template, proxies)
        template["rule-providers"].update(self._blacklist_http_rule_providers())
        template["rules"].extend(BLACKLIST_RULES)

        return template, userinfo

    def query2sub(self, urls: str, agents: str, names: str):
        url_list = urls.split(",") if urls and urls.strip() else []
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


generator_instance = None


def init_generator(config: ClashConfig):
    global generator_instance
    generator_instance = ClashYamlGenerator(config)


def get_generator():
    global generator_instance
    if generator_instance is None:
        raise RuntimeError("ClashYamlGenerator not initialized")
    return generator_instance


def get_generator_dependency():
    return Depends(get_generator)
