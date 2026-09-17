"""夸克网盘自动签到 CLI。

环境变量:
    COOKIE_QUARK: 多账户用 回车 或 && 分开。
        新格式: user=张三; url=https://drive-m.quark.cn/1/clouddrive/act/growth/reward?...&kps=xxx&sign=xxx&vcode=xxx;
        旧格式: user=张三; kps=xxx; sign=xxx; vcode=xxx;
"""

import os
import re

import requests
import typer
from dotenv import load_dotenv

from utils.logger import get_logger
from utils.notify import send

logger = get_logger(__name__)
app = typer.Typer(help="夸克网盘自动签到")


# ---------------------------------------------------------------------------
# 核心逻辑（改编自 checkIn_Quark.py）
# ---------------------------------------------------------------------------


def _convert_bytes(b: float) -> str:
    """将字节转换为人类可读格式 (B/KB/MB/GB/TB/...)"""
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024
        i += 1
    return f"{b:.2f} {units[i]}"


def _extract_params(url: str) -> dict:
    """从完整 URL 中提取 kps / sign / vcode 参数"""
    query_start = url.find("?")
    query_string = url[query_start + 1 :] if query_start != -1 else ""

    params = {}
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value

    return {
        "kps": params.get("kps", ""),
        "sign": params.get("sign", ""),
        "vcode": params.get("vcode", ""),
    }


class _Quark:
    """夸克签到 API 封装（内部类，不对外暴露）"""

    def __init__(self, user_data: dict):
        self.param = user_data

    # ---- API ----

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        resp = requests.get(url, params=self._qs(pr="ucpro", fr="android")).json()
        return resp.get("data") or False

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        resp = requests.post(
            url, json={"sign_cyclic": True}, params=self._qs(pr="ucpro", fr="android")
        ).json()
        if resp.get("data"):
            return True, resp["data"]["sign_daily_reward"]
        return False, resp.get("message", "未知错误")

    def query_balance(self):
        url = "https://coral2.quark.cn/currency/v1/queryBalance"
        resp = requests.get(
            url,
            params={
                "moduleCode": "1f3563d38896438db994f118d4ff53cb",
                "kps": self.param.get("kps"),
            },
        ).json()
        if resp.get("data"):
            return resp["data"]["balance"]
        return resp.get("msg", "未知错误")

    # ---- 业务入口 ----

    def do_sign(self) -> str:
        log = ""
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
                f"💾 网盘总容量：{_convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量："
            )
            comp = growth_info.get("cap_composition", {})
            if "sign_reward" in comp:
                log += f"{_convert_bytes(comp['sign_reward'])}\n"
            else:
                log += "0 MB\n"

            cap_sign = growth_info["cap_sign"]
            if cap_sign["sign_daily"]:
                log += (
                    f"✅ 签到日志: 今日已签到+{_convert_bytes(cap_sign['sign_daily_reward'])}，"
                    f"连签进度({cap_sign['sign_progress']}/{cap_sign['sign_target']})\n"
                )
            else:
                ok, ret = self.get_growth_sign()
                if ok:
                    log += (
                        f"✅ 执行签到: 今日签到+{_convert_bytes(ret)}，"
                        f"连签进度({cap_sign['sign_progress'] + 1}/{cap_sign['sign_target']})\n"
                    )
                else:
                    log += f"❌ 签到异常: {ret}\n"
        else:
            log += "❌ 签到异常: 获取成长信息失败\n"

        return log

    # ---- 内部工具 ----

    def _qs(self, **extra) -> dict:
        """构造请求公共 query string 参数"""
        qs = {
            "kps": self.param.get("kps"),
            "sign": self.param.get("sign"),
            "vcode": self.param.get("vcode"),
        }
        qs.update(extra)
        return qs


# ---------------------------------------------------------------------------
# CLI 子命令
# ---------------------------------------------------------------------------


@app.command()
def sign(
    dotenv_path: str = typer.Option(".env", "--env", "-e", help="dotenv 文件路径"),
    notify_flag: bool = typer.Option(True, "--notify/--no-notify", help="是否发送通知"),
):
    """执行夸克网盘每日签到。

    需要 .env 中配置 COOKIE_QUARK。多账户用 回车 或 && 分隔。
    """
    load_dotenv(dotenv_path)

    raw = os.getenv("COOKIE_QUARK")
    if not raw:
        logger.error("未添加 COOKIE_QUARK 环境变量")
        raise typer.Exit(1)

    # 解析多账户
    cookie_list = re.split(r"\n|&&", raw)
    cookie_list = [c.strip() for c in cookie_list if c.strip()]

    typer.secho(f"✅ 检测到共 {len(cookie_list)} 个夸克账号\n", fg=typer.colors.GREEN)

    msg = ""
    for i, raw_account in enumerate(cookie_list):
        # 解析 user_data
        user_data: dict = {}
        for part in raw_account.replace(" ", "").split(";"):
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            user_data[k] = v

        # 从 url 中提取 kps / sign / vcode（兼容新格式）
        if "url" in user_data:
            user_data.update(_extract_params(user_data["url"]))

        # 必须的参数检查
        missing = [k for k in ("kps", "sign", "vcode") if not user_data.get(k)]
        if missing:
            msg += f"🙍🏻‍♂️ 第{i + 1}个账号 ❌ 缺少参数: {', '.join(missing)}\n"
            logger.warning("账号 %s 缺少参数: %s", i + 1, missing)
            continue

        msg += f"🙍🏻‍♂️ 第{i + 1}个账号\n"
        result = _Quark(user_data).do_sign()
        msg += result + "\n"

        # 实时打印
        typer.echo(f"🙍🏻‍♂️ 第{i + 1}个账号 {user_data.get('user', '(未命名)')}")
        typer.echo(result)

    # 发送通知
    if notify_flag and msg:
        try:
            send("夸克自动签到", msg)
        except Exception:
            logger.exception("发送通知失败")

    # 返回给调用者（方便编程调用）
    typer.secho("\n----------夸克网盘签到完毕----------", fg=typer.colors.CYAN)


@app.command()
def check(
    dotenv_path: str = typer.Option(".env", "--env", "-e", help="dotenv 文件路径"),
):
    """检查 COOKIE_QUARK 是否配置，以及每个账号的成长信息。"""
    load_dotenv(dotenv_path)

    raw = os.getenv("COOKIE_QUARK")
    if not raw:
        logger.error("未添加 COOKIE_QUARK 环境变量")
        raise typer.Exit(1)

    cookie_list = re.split(r"\n|&&", raw)
    cookie_list = [c.strip() for c in cookie_list if c.strip()]

    typer.secho(f"✅ 检测到共 {len(cookie_list)} 个夸克账号\n", fg=typer.colors.GREEN)

    for i, raw_account in enumerate(cookie_list):
        user_data: dict = {}
        for part in raw_account.replace(" ", "").split(";"):
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            user_data[k] = v
        if "url" in user_data:
            user_data.update(_extract_params(user_data["url"]))

        typer.secho(
            f"🙍🏻‍♂️ 第{i + 1}个账号 {user_data.get('user', '(未命名)')}",
            fg=typer.colors.CYAN,
        )

        missing = [k for k in ("kps", "sign", "vcode") if not user_data.get(k)]
        if missing:
            typer.secho(f"  ❌ 缺少参数: {', '.join(missing)}", fg=typer.colors.RED)
            continue

        growth = _Quark(user_data).get_growth_info()
        if growth:
            typer.secho(
                f"  👤 {'88VIP' if growth['88VIP'] else '普通用户'} | "
                f"💾 {_convert_bytes(growth['total_capacity'])} | "
                f"✅今日已签到={growth['cap_sign']['sign_daily']}",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho("  ❌ 获取成长信息失败（参数可能已过期）", fg=typer.colors.RED)


if __name__ == "__main__":
    app()
