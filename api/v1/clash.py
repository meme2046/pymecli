import base64

import yaml
from fastapi import APIRouter, Query, Response

from core.clash import ClashYamlGenerator, get_generator_dependency

router = APIRouter()

# base64 解码后 YAML 最大 64KB，防止恶意超大请求
_MAX_CUSTOM_YAML_BYTES = 64 * 1024


def _parse_custom_proxies(custom_b64: str | None) -> list:
    """把 base64 编码的 custom.yaml 解码，只提取 proxies 列表"""
    if not custom_b64:
        return []
    try:
        raw = base64.b64decode(custom_b64)
        if len(raw) > _MAX_CUSTOM_YAML_BYTES:
            return []
        cfg = yaml.safe_load(raw.decode("utf-8"))
        if not isinstance(cfg, dict):
            return []
        return cfg.get("proxies", []) or []
    except Exception:
        return []


class NoAnchorDumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True


@router.get(
    "/subpw",
    summary="转换订阅(可以转换多个订阅),proxy-providers方式合并多个订阅,白名单模式",
    description="根据提供的URL、User-Agent和名称获取并处理订阅信息,返回YAML格式的Clash配置",
    response_description="返回YAML格式的Clash配置文件",
)
async def subProviderWhite(
    urls: str = Query(..., description="订阅URL,逗号分隔"),
    agents: str = Query(
        "clash-verge/v2.4.3",
        description="User-Agent,逗号分隔(根据客户段选择)",
    ),
    names: str = Query(
        "订阅1", description="订阅名称,逗号分隔(可选,在客户端中的显示名)"
    ),
    custom: str | None = Query(
        None,
        description="自定义clash配置(base64编码,可选,只提取proxies节点合并)",
    ),
    generator: ClashYamlGenerator = get_generator_dependency(),
):
    # 将JSON字符串解析为Python对象
    sub_list = generator.query2sub(urls, agents, names)
    custom_proxies = _parse_custom_proxies(custom)
    yaml_content, userinfo = generator.genPW(sub_list, custom_proxies)
    yaml_string = yaml.dump(
        yaml_content,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        # Dumper=NoAnchorDumper,
    )
    return Response(
        headers={"Subscription-Userinfo": userinfo},
        content=yaml_string,
        media_type="text/yaml",
    )


@router.get(
    "/subpb",
    summary="转换订阅(可以转换多个订阅),proxy-providers方式合并多个订阅, 黑名单模式",
    description="根据提供的URL、User-Agent和名称获取并处理订阅信息,返回YAML格式的Clash配置",
    response_description="返回YAML格式的Clash配置文件",
)
async def subProviderBlack(
    urls: str = Query(..., description="订阅URL,逗号分隔"),
    agents: str = Query(
        "clash-verge/v2.4.3",
        description="User-Agent,逗号分隔(根据客户段选择)",
    ),
    names: str = Query(
        "订阅1", description="订阅名称,逗号分隔(可选,在客户端中的显示名)"
    ),
    custom: str | None = Query(
        None,
        description="自定义clash配置(base64编码,可选,只提取proxies节点合并)",
    ),
    generator: ClashYamlGenerator = get_generator_dependency(),
):
    # 将JSON字符串解析为Python对象
    sub_list = generator.query2sub(urls, agents, names)
    custom_proxies = _parse_custom_proxies(custom)
    yaml_content, userinfo = generator.genPB(sub_list, custom_proxies)
    yaml_string = yaml.dump(
        yaml_content,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        # Dumper=NoAnchorDumper,
    )
    return Response(
        headers={"Subscription-Userinfo": userinfo},
        content=yaml_string,
        media_type="text/yaml",
    )


@router.get(
    "/subb",
    summary="转换订阅(可以转换多个订阅),拼接proxies的方式合并多个订阅, 黑名单模式",
    description="根据提供的URL、User-Agent和名称获取并处理订阅信息,返回YAML格式的Clash配置",
    response_description="返回YAML格式的Clash配置文件",
)
async def subBlack(
    urls: str = Query(..., description="订阅URL,逗号分隔"),
    agents: str = Query(
        "clash-verge/v2.4.3",
        description="User-Agent,逗号分隔(根据客户段选择)",
    ),
    names: str = Query(
        "订阅1", description="订阅名称,逗号分隔(可选,在客户端中的显示名)"
    ),
    custom: str | None = Query(
        None,
        description="自定义clash配置(base64编码,可选,只提取proxies节点合并)",
    ),
    generator: ClashYamlGenerator = get_generator_dependency(),
):
    # 将JSON字符串解析为Python对象
    sub_list = generator.query2sub(urls, agents, names)
    custom_proxies = _parse_custom_proxies(custom)
    yaml_content, userinfo = generator.genB(sub_list, custom_proxies)
    yaml_string = yaml.dump(
        yaml_content,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        # Dumper=NoAnchorDumper,
    )
    return Response(
        headers={"Subscription-Userinfo": userinfo},
        content=yaml_string,
        media_type="text/yaml",
    )
