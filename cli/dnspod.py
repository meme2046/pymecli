"""DNSPod DDNS 自动更新 CLI。

环境变量 (Go 版命名保持一致):
    DP_ID:         DNSPod 登录 ID
    DP_TOKEN:      DNSPod 登录 Token
    DP_DOMAIN:     域名 (如 cursor.email)
    DP_RECORD_ID:  IPv4 A 记录 ID
    DP_RECORD_ID_IPV6: IPv6 AAAA 记录 ID
    DP_SUB_DOMAIN: 子域名前缀 (默认 "api")
    DP_RECORD_LINE: 记录线路 (默认 "默认")

Redis 依赖 (用于 IPv6 DDNS):
    REDIS_URL:     Redis 地址，key = "local.IPv6"
"""
import os
import re

import requests
import typer
from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer(help="DNSPod DDNS 自动更新")


API_BASE = "https://dnsapi.cn"


# ---------------------------------------------------------------------------
# 底层 API
# ---------------------------------------------------------------------------

def _call(action: str, data: dict) -> dict:
    """通用 DNSPod API 调用（form-urlencoded POST）"""
    resp = requests.post(f"{API_BASE}/{action}", data=data, timeout=15)
    resp.raise_for_status()
    body = resp.json()

    status = body.get("status", {})
    code = str(status.get("code", ""))
    if code != "1":
        msg = status.get("message", "未知错误")
        raise RuntimeError(f"DNSPod API 错误 [{code}]: {msg}")

    return body


def record_modify(
    login_token: str,
    domain: str,
    record_id: str,
    sub_domain: str,
    record_type: str,
    value: str,
    record_line: str = "默认",
) -> dict:
    """调用 Record.Modify 修改 DNS 记录"""
    data = {
        "login_token": login_token,
        "format": "json",
        "domain": domain,
        "record_id": record_id,
        "sub_domain": sub_domain,
        "record_type": record_type,
        "record_line": record_line,
        "value": value,
    }
    return _call("Record.Modify", data)


def record_list(login_token: str, domain: str) -> list[dict]:
    """调用 Record.List 列出域名下所有记录"""
    data = {
        "login_token": login_token,
        "format": "json",
        "domain": domain,
    }
    body = _call("Record.List", data)
    return body.get("records", [])


def get_public_ipv4() -> str:
    """从 ip.3322.net 获取公网 IPv4（纯文本）"""
    resp = requests.get("http://ip.3322.net", timeout=10)
    resp.raise_for_status()
    ip = resp.text.strip()
    # 简单校验
    if not re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
        raise RuntimeError(f"获取到的不是有效 IPv4: {ip!r}")
    return ip


def get_public_ipv6() -> str:
    """从 Redis 读取公网 IPv6（key=local.IPv6）"""
    from utils.pyredis import get_redis_client_sync

    r = get_redis_client_sync()
    try:
        val = r.get("local.IPv6")
        if not val:
            raise RuntimeError("Redis 中 local.IPv6 为空")
        return val.strip()
    finally:
        r.close()


# ---------------------------------------------------------------------------
# CLI 子命令
# ---------------------------------------------------------------------------

def _require_env(env_path: str) -> dict:
    """加载 dotenv 并返回公共配置"""
    load_dotenv(env_path)
    dp_id = os.getenv("DP_ID")
    dp_token = os.getenv("DP_TOKEN")
    dp_domain = os.getenv("DP_DOMAIN")

    missing = []
    if not dp_id:
        missing.append("DP_ID")
    if not dp_token:
        missing.append("DP_TOKEN")
    if not dp_domain:
        missing.append("DP_DOMAIN")
    if missing:
        logger.error("缺少环境变量: %s", ", ".join(missing))
        raise typer.Exit(1)

    return {
        "login_token": f"{dp_id},{dp_token}",
        "domain": dp_domain,
        "sub_domain": os.getenv("DP_SUB_DOMAIN", "api"),
        "record_line": os.getenv("DP_RECORD_LINE", "默认"),
    }


@app.command()
def list(
    dotenv_path: str = typer.Option(".env", "--env", "-e", help="dotenv 文件路径"),
):
    """列出域名下所有 DNS 记录（方便查 record_id）"""
    cfg = _require_env(dotenv_path)

    records = record_list(cfg["login_token"], cfg["domain"])
    if not records:
        typer.secho("没有记录", fg=typer.colors.YELLOW)
        return

    typer.secho(f"\n域名 {cfg['domain']} 共 {len(records)} 条记录:\n", fg=typer.colors.CYAN)
    typer.secho(f"{'ID':<10} {'类型':<6} {'子域':<16} {'值':<30} {'状态'}", fg=typer.colors.GREEN)
    typer.secho("-" * 80, fg=typer.colors.CYAN)
    for r in records:
        typer.echo(
            f"{r['id']:<10} {r['type']:<6} {r['name']:<16} {r['value']:<30} {r['status']}"
        )


@app.command()
def ddns(
    dotenv_path: str = typer.Option(".env", "--env", "-e", help="dotenv 文件路径"),
    force: bool = typer.Option(False, "--force", help="IP 未变化也强制更新"),
):
    """更新 A 记录（IPv4 DDNS）"""
    cfg = _require_env(dotenv_path)

    record_id = os.getenv("DP_RECORD_ID")
    if not record_id:
        logger.error("缺少环境变量: DP_RECORD_ID")
        raise typer.Exit(1)

    try:
        cur_ip = get_public_ipv4()
    except Exception as e:
        logger.exception("获取公网 IPv4 失败: %s", e)
        raise typer.Exit(1)

    typer.secho(f"当前公网 IPv4: {cur_ip}", fg=typer.colors.CYAN)

    # 获取现有记录对比
    records = record_list(cfg["login_token"], cfg["domain"])
    existing = next((r for r in records if r["id"] == record_id), None)
    if existing and existing["value"] == cur_ip and not force:
        typer.secho(f"IP 未变化 ({cur_ip})，跳过更新", fg=typer.colors.YELLOW)
        return

    try:
        resp = record_modify(
            login_token=cfg["login_token"],
            domain=cfg["domain"],
            record_id=record_id,
            sub_domain=cfg["sub_domain"],
            record_type="A",
            value=cur_ip,
            record_line=cfg["record_line"],
        )
        typer.secho(
            f"✅ A 记录更新成功 | "
            f"新地址: {resp['record']['value']} | "
            f"接口返回: {resp['status']['message']}",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        logger.exception("A 记录更新失败: %s", e)
        raise typer.Exit(1)


@app.command()
def ddns6(
    dotenv_path: str = typer.Option(".env", "--env", "-e", help="dotenv 文件路径"),
    force: bool = typer.Option(False, "--force", help="IP 未变化也强制更新"),
):
    """更新 AAAA 记录（IPv6 DDNS，从 Redis 读取 IPv6）"""
    cfg = _require_env(dotenv_path)

    record_id = os.getenv("DP_RECORD_ID_IPV6")
    if not record_id:
        logger.error("缺少环境变量: DP_RECORD_ID_IPV6")
        raise typer.Exit(1)

    try:
        cur_ip = get_public_ipv6()
    except Exception as e:
        logger.exception("获取公网 IPv6 失败: %s", e)
        raise typer.Exit(1)

    typer.secho(f"当前公网 IPv6: {cur_ip}", fg=typer.colors.CYAN)

    # 获取现有记录对比
    records = record_list(cfg["login_token"], cfg["domain"])
    existing = next((r for r in records if r["id"] == record_id), None)
    if existing and existing["value"] == cur_ip and not force:
        typer.secho(f"IPv6 未变化 ({cur_ip})，跳过更新", fg=typer.colors.YELLOW)
        return

    try:
        resp = record_modify(
            login_token=cfg["login_token"],
            domain=cfg["domain"],
            record_id=record_id,
            sub_domain=cfg["sub_domain"],
            record_type="AAAA",
            value=cur_ip,
            record_line=cfg["record_line"],
        )
        typer.secho(
            f"✅ AAAA 记录更新成功 | "
            f"新地址: {resp['record']['value']} | "
            f"接口返回: {resp['status']['message']}",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        logger.exception("AAAA 记录更新失败: %s", e)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
