import os

import typer
from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer()


@app.command()
def info(
    dotenv_path: str = typer.Argument(
        help="dotenv file contains TELE_SEESION_STRING", default=".env"
    ),
):
    load_dotenv(dotenv_path)
    logger.info(os.getenv("TELE_SESSION_STRING"))


@app.command()
def check(
    dotenv_path: str = typer.Argument(
        help="dotenv file contains TELE_SESSION_STRING / TELE_API_ID / TELE_API_HASH",
        default=".env",
    ),
):
    """验证 TELE_SESSION_STRING 是否有效。

    通过 StringSession 建立客户端并发起一次 get_me 调用：
    能正常返回账号对象即视为 session 有效；get_me 在 auth_key
    未授权 / 被注销时会内部捕获 UnauthorizedError 并返回 None，
    故 me is None 即判定 session 失效。
    需要 .env 中同时配置 TELE_API_ID 与 TELE_API_HASH。
    """
    load_dotenv(dotenv_path)

    session_string = os.getenv("TELE_SESSION_STRING")
    api_id = os.getenv("TELE_API_ID")
    api_hash = os.getenv("TELE_API_HASH")
    if not session_string:
        logger.error("TELE_SESSION_STRING 未找到: %s", dotenv_path)
        raise typer.Exit(1)
    if not (api_id and api_hash):
        logger.error("TELE_API_ID / TELE_API_HASH 未找到: %s", dotenv_path)
        raise typer.Exit(1)

    # 延迟导入：仅在使用 check 子命令时才加载 telethon，避免拖慢其它子命令
    import asyncio
    from typing import Awaitable, cast

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    async def _verify():
        client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
        try:
            await client.connect()
            # get_me 会真正发起一次 API 调用，能返回即说明 auth_key 仍然有效
            return await client.get_me()
        finally:
            # telethon 的 disconnect 声明为同步 def，但 loop 运行时实际返回协程，
            # Pylance 据签名推断返回 None 导致 await 报错，用 cast 显式标注
            await cast(Awaitable[None], client.disconnect())

    try:
        me = asyncio.run(_verify())
    except Exception as e:
        # 网络异常等非鉴权问题，打印完整堆栈便于排查
        logger.exception("验证 session 时发生异常: %s", e)
        raise typer.Exit(1)

    # get_me 内部 catch UnauthorizedError（含 AuthKeyUnregistered/Invalid 等所有子类）后返回 None，
    # 所以 me is None 才是 auth_key 已被服务器拒绝 / session 失效的真实信号
    if me is None:
        logger.error("session 无效: auth_key 未授权或已被服务器注销")
        raise typer.Exit(1)

    logger.info(
        "session 有效: id=%s name=%s phone=%s",
        getattr(me, "id", None), getattr(me, "first_name", None), getattr(me, "phone", None),
    )


@app.command()
def login(
    dotenv_path: str = typer.Argument(
        help="dotenv file containing TELE_API_ID / TELE_API_HASH",
        default=".env",
    ),
):
    """交互式登录并打印 TELE_SESSION_STRING。

    使用 telethon 的 start() 完成 phone → 验证码 → 2FA 的交互式登录，
    登录成功后用 StringSession.save() 取出可复用 session 串并打印。
    session string 失效周期很长，手动复制到 .env 即可，不做自动回写。
    需要 .env 中已配置 TELE_API_ID 与 TELE_API_HASH。
    """
    load_dotenv(dotenv_path)
    api_id = os.getenv("TELE_API_ID")
    api_hash = os.getenv("TELE_API_HASH")
    if not (api_id and api_hash):
        logger.error("TELE_API_ID / TELE_API_HASH 未找到: %s", dotenv_path)
        raise typer.Exit(1)

    # 延迟导入：仅在使用 login 子命令时才加载 telethon
    import asyncio
    from typing import Awaitable, cast

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    async def _login():
        # 空 StringSession + start() 触发交互式登录（控制台输入 phone / 验证码 / 2FA 密码）
        session = StringSession()
        client = TelegramClient(session, int(api_id), api_hash)
        try:
            # start() 同 disconnect 一样声明为同步 def，loop 运行时返回协程，用 cast 标注
            await cast(Awaitable[None], client.start())
            # telethon 在 connect 时原地写入 session.auth_key，故持有的 session 引用即登录后状态；
            # 直接用 session.save() 而非 client.session，避开 client.session 宽类型推断的 .save() 报错
            return session.save()
        finally:
            await cast(Awaitable[None], client.disconnect())

    try:
        session_string = asyncio.run(_login())
    except Exception as e:
        logger.exception("生成 session string 时发生异常: %s", e)
        raise typer.Exit(1)

    # 只打印，不自动回写 .env：session string 失效周期长，手动加一次即可，避免覆盖风险
    typer.secho("TELE_SESSION_STRING 生成成功，请复制下行并手动写入 .env：", fg=typer.colors.GREEN)
    typer.secho(session_string, fg=typer.colors.CYAN)


@app.command()
def upload(
    image_path: str = typer.Argument(
        help="要上传的图片文件路径",
    ),
    dotenv_path: str = typer.Option(
        help="dotenv file path", default=".env"
    ),
):
    """上传图片到指定 Telegram 频道。

    使用 TELE_SESSION_STRING 登录并上传图片到 TELE_ONEDAOSHARE 环境变量指定的频道。
    """
    load_dotenv(dotenv_path)

    session_string = os.getenv("TELE_SESSION_STRING")
    api_id = os.getenv("TELE_API_ID")
    api_hash = os.getenv("TELE_API_HASH")
    channel = os.getenv("TELE_ONEDAOSHARE")

    if not session_string:
        logger.error("TELE_SESSION_STRING 未找到: %s", dotenv_path)
        raise typer.Exit(1)
    if not (api_id and api_hash):
        logger.error("TELE_API_ID / TELE_API_HASH 未找到: %s", dotenv_path)
        raise typer.Exit(1)
    if not channel:
        logger.error("TELE_ONEDAOSHARE 未找到: %s", dotenv_path)
        raise typer.Exit(1)
    if not os.path.isfile(image_path):
        logger.error("图片文件不存在: %s", image_path)
        raise typer.Exit(1)

    import asyncio
    from typing import Awaitable, cast

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    async def _upload():
        client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.error("session 无效或已失效，请先运行 login 命令重新生成")
                raise typer.Exit(1)
            
            # 规范化频道 ID：如果是纯数字，自动加 -100 前缀
            target = channel.strip()
            if target.isdigit():
                target = f"-100{target}"
                logger.info("频道 ID 已自动规范化为: %s", target)
            
            target_id = int(target) if target.lstrip('-').isdigit() else None
            
            # 方法1：先尝试直接通过 ID 在 dialogs 缓存中查找（更可靠）
            logger.info("正在查找频道: %s", target)
            found_dialog = None
            async for dialog in client.iter_dialogs():
                if dialog.id == target_id:
                    found_dialog = dialog
                    break
            
            if found_dialog:
                logger.info("成功找到频道: %s (ID: %s)", target, found_dialog.id)
                # 使用 dialog.entity 作为目标，避免再次解析
                target = found_dialog.entity
            else:
                # 方法2：退回到 get_entity（支持 @username 等）
                logger.info("缓存中未找到，尝试通过 get_entity 解析: %s", target)
                try:
                    entity = await client.get_entity(target)
                    if isinstance(entity, list):
                        entity = entity[0]
                    logger.info("成功解析: %s (ID: %s)", target, getattr(entity, 'id', 'N/A'))
                    target = entity
                except ValueError as e:
                    logger.error(
                        "无法访问频道 %s。请检查：\n"
                        "1. ID 是否正确（纯数字需要带 -100 前缀）\n"
                        "2. 当前登录的账号是否为该频道成员\n"
                        "3. 如果是私有名片，请使用频道的 @username\n"
                        "错误详情: %s", target, e
                    )
                    raise typer.Exit(1)
            
            # 发送文件到频道，force_document=False 表示作为图片发送（Telegram 会自动压缩）
            # 如果想原样发送文件，设置 force_document=True
            result = await client.send_file(
                target,
                image_path,
                caption="",  # 可以自定义描述
                force_document=False,
            )
            
            # send_file 可能返回 Message 或 List[Message]
            message = result[0] if isinstance(result, list) else result
            
            # 下载媒体文件到本地临时目录
            download_link = None
            try:
                if hasattr(message, 'media') and message.media:
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    local_path = await client.download_media(
                        message,
                        file=temp_dir
                    )
                    if local_path:
                        download_link = local_path
            except Exception as e:
                logger.debug("下载文件失败: %s", e)
            
            return message, download_link
        finally:
            await cast(Awaitable[None], client.disconnect())

    try:
        message, download_link = asyncio.run(_upload())
        
        # 打印详细的上传响应信息
        typer.secho("\n📤 上传成功！", fg=typer.colors.GREEN, bold=True)
        typer.secho("-" * 50, fg=typer.colors.CYAN)
        typer.secho(f"  消息 ID: {message.id}", fg=typer.colors.WHITE)
        typer.secho(f"  频道: {channel}", fg=typer.colors.WHITE)
        
        # 尝试获取文件信息
        if hasattr(message, 'media') and message.media:
            media = message.media
            # 递归打印完整结构（类似 JSON 格式）
            typer.secho(f"  Media 类型: {type(media).__name__}", fg=typer.colors.YELLOW)
        
        # 打印下载的本地文件路径（telesco.pe 公网链接 telethon 无法直接获取）
        if download_link:
            typer.secho(f"\n  � 本地下载路径:", fg=typer.colors.MAGENTA, bold=True)
            typer.secho(f"  {download_link}", fg=typer.colors.MAGENTA)
        
        # 打印消息链接（如果可能）
        if hasattr(message, 'chat') and message.chat:
            chat_id = getattr(message.chat, 'id', None)
            if chat_id:
                typer.secho(f"  聊天 ID: {chat_id}", fg=typer.colors.WHITE)
        
        typer.secho("-" * 50, fg=typer.colors.CYAN)
    except typer.Exit:
        raise  # 重新抛出 typer.Exit 以保持退出码
    except Exception as e:
        logger.exception("上传图片时发生异常: %s", e)
        raise typer.Exit(1)


@app.command()
def list_channels(
    dotenv_path: str = typer.Option(
        help="dotenv file path", default=".env"
    ),
):
    """列出当前账号加入的所有频道及其 ID。

    方便获取正确的频道 ID 填入 TELE_ONE_DAO_SHARE。
    """
    load_dotenv(dotenv_path)

    session_string = os.getenv("TELE_SESSION_STRING")
    api_id = os.getenv("TELE_API_ID")
    api_hash = os.getenv("TELE_API_HASH")

    if not session_string:
        logger.error("TELE_SESSION_STRING 未找到: %s", dotenv_path)
        raise typer.Exit(1)
    if not (api_id and api_hash):
        logger.error("TELE_API_ID / TELE_API_HASH 未找到: %s", dotenv_path)
        raise typer.Exit(1)

    import asyncio
    from typing import Awaitable, cast

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    async def _list():
        client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.error("session 无效或已失效，请先运行 login 命令重新生成")
                raise typer.Exit(1)
            
            channels = []
            async for dialog in client.iter_dialogs():
                if dialog.is_channel:
                    channels.append(dialog)
            return channels
        finally:
            await cast(Awaitable[None], client.disconnect())

    try:
        channels = asyncio.run(_list())
        if not channels:
            typer.secho("你还没有加入任何频道", fg=typer.colors.YELLOW)
            return
        
        typer.secho(f"\n你加入的 {len(channels)} 个频道：\n", fg=typer.colors.GREEN)
        typer.secho(f"{'频道名称':<40} {'ID':<25}", fg=typer.colors.CYAN)
        typer.secho("-" * 65, fg=typer.colors.CYAN)
        for ch in channels:
            name = ch.name or "(无名称)"
            typer.secho(f"{name:<40} {ch.id:<25}")
        typer.secho("\n提示：复制 ID（如 -100xxxxxxxx）到 .env 的 TELE_ONEDAOSHARE", fg=typer.colors.YELLOW)
    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("列出频道时发生异常: %s", e)
        raise typer.Exit(1)


if __name__ == "__main__":
    logger.info("main")
