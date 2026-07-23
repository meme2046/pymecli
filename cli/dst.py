import re
from typing import Dict, List, Optional

import requests
import typer
from slpp import slpp as lua

app = typer.Typer()

STEAM_API_URL = (
    "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v0001"
)


def get_mod_versions(workshop_ids: List[str]) -> Dict[str, Dict[str, Optional[str]]]:
    if not workshop_ids:
        return {}

    data = {"itemcount": str(len(workshop_ids))}
    for i, wid in enumerate(workshop_ids):
        data[f"publishedfileids[{i}]"] = wid

    try:
        response = requests.post(STEAM_API_URL, data=data, timeout=15)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        typer.secho(f"✗ Steam API 请求失败: {e}", fg=typer.colors.RED)
        return {}

    versions: Dict[str, Dict[str, Optional[str]]] = {}
    for detail in result["response"].get("publishedfiledetails", []):
        publishedfileid = detail.get("publishedfileid")
        title = detail.get("title")
        tags = detail.get("tags", [])
        version = None
        for tag in tags:
            tag_str = tag.get("tag", "")
            if tag_str.startswith("version:"):
                version = tag_str.replace("version:", "")
                break
        versions[publishedfileid] = {"version": version, "title": title}

    return versions


def extract_workshop_id(key: str) -> Optional[str]:
    match = re.match(r"workshop-(\d+)", key)
    return match.group(1) if match else None


def parse_lua_file(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    source = source.strip()
    if source.startswith("return"):
        source = source[6:].strip()
    result = lua.decode(source)
    assert isinstance(result, dict)
    return result


def write_lua_file(file_path: str, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("return " + lua.encode(data) + "\n")


def get_client_mods(file_path: str, mod_id: str) -> Optional[tuple[dict, dict]]:
    """
    解析 lua 文件，返回 (data, client_mods)。
    失败返回 None(错误信息已由函数自行打印)。
    """
    try:
        data = parse_lua_file(file_path)
    except FileNotFoundError:
        typer.secho(f"✗ 文件不存在: {file_path}", fg=typer.colors.RED)
        return None
    except Exception as e:
        typer.secho(f"✗ 解析 Lua 文件失败: {e}", fg=typer.colors.RED)
        return None

    main_mod_key = f"workshop-{mod_id}"
    main_mod = data.get(main_mod_key)
    if not main_mod:
        typer.secho(f"✗ 未找到 {main_mod_key}", fg=typer.colors.RED)
        return data, {}

    client_mods = main_mod.get("configuration_options", {}).get("client_mods_list", {})
    if not client_mods:
        typer.secho("✗ 未找到 client_mods", fg=typer.colors.RED)
        return data, {}

    return data, client_mods


# update_client_mods
@app.command()
def convert_update(
    file_path: str = typer.Argument(
        "d:/github/meme2046/docker/dst/modoverrides.lua",
        help="modoverrides.lua 文件路径",
    ),
    mod_id: str = typer.Option(
        "3486375086",
        "--mod-id",
        "-m",
        help="模组: 客户端Mod转为服务器Mod<3486375086>的ID, 固定值",
    ),
    output: List[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="额外的输出路径，可多次指定",
    ),
):
    """
    更新modoverrides.lua中<3486375086>的mods的版本信息
    """
    result = get_client_mods(file_path, mod_id)
    if result is None:
        raise typer.Exit(code=1)
    data, client_mods = result

    workshop_ids = []
    for key in client_mods.keys():
        wid = extract_workshop_id(key)
        if wid:
            workshop_ids.append(wid)

    if not workshop_ids:
        typer.secho("✗ 未找到任何 client_mods", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(
        f"🔍 发现 {len(workshop_ids)} 个 client mods, 正在查询 Steam API...",
        fg=typer.colors.BLUE,
    )
    versions = get_mod_versions(workshop_ids)

    if not versions:
        typer.secho("✗ 未能获取steam版本信息", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho("📝 正在更新版本号...", fg=typer.colors.BLUE)
    updated_count = 0
    for mod_key, mod_info in client_mods.items():
        wid = extract_workshop_id(mod_key)
        if not wid:
            continue
        mod_data = versions.get(wid)
        if mod_data is None:
            typer.secho(f"⚠️  {mod_key}: 未获取到版本信息", fg=typer.colors.YELLOW)
            continue
        new_version = mod_data.get("version")
        title = mod_data.get("title", "")
        if new_version is None:
            typer.secho(
                f"⚠️  {mod_key} ({title}): 未获取到版本信息", fg=typer.colors.YELLOW
            )
            continue
        old_version = mod_info.get("version")
        if old_version != new_version:
            mod_info["version"] = new_version
            updated_count += 1
            typer.secho(
                f"✅ {mod_key} ({title}): {old_version} -> {new_version}",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho(
                f"{mod_key} ({title}): 已是最新版本 {old_version}",
                fg=typer.colors.WHITE,
            )

    try:
        if updated_count > 0:
            write_lua_file(file_path, data)
            typer.secho(f"💾 已保存到: {file_path}", fg=typer.colors.CYAN)
        if output:
            for p in output:
                write_lua_file(p, data)
                typer.secho(f"💾 已保存到: {p}", fg=typer.colors.CYAN)
    except Exception as e:
        typer.secho(f"✗ 写入文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if updated_count > 0:
        typer.secho(f"🎉 成功更新 {updated_count} 个 mod 版本", fg=typer.colors.GREEN)
    else:
        typer.secho("⬆️ 所有MOD已是最新版本", fg=typer.colors.YELLOW)


@app.command()
def mod_setup(
    file_path: str = typer.Argument(
        "d:/github/meme2046/docker/dst/modoverrides.lua",
        help="modoverrides.lua 文件路径",
    ),
    mod_id: str = typer.Option(
        "3486375086",
        "--mod-id",
        "-m",
        help="模组: 客户端Mod转为服务器Mod<3486375086>的ID, 固定值",
    ),
    output: List[str] = typer.Option(
        ["dedicated_server_mods_setup.lua"],
        "--output",
        "-o",
        help="mods_setup输出路径,可多次指定",
    ),
):
    """
    列出所有 mod, 并以<dedicated_server_mods_setup>格式保存到指定文件
    """
    result = get_client_mods(file_path, mod_id)
    if result is None:
        raise typer.Exit(code=1)
    data, client_mods = result

    client_ids = []
    for key in client_mods.keys():
        wid = extract_workshop_id(key)
        if wid:
            client_ids.append(wid)

    server_ids = []
    for key in data.keys():
        wid = extract_workshop_id(key)
        if wid:
            server_ids.append(wid)

    versions = get_mod_versions(server_ids + client_ids)

    if not versions:
        typer.secho("✗ 未能获取steam版本信息", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    setup_list = []

    typer.secho(
        f"📢 server_mods({len(server_ids)}):",
        fg=typer.colors.GREEN,
    )

    for item in server_ids:
        mod_data = versions.get(item)

        if mod_data is None:
            typer.secho(f"✗ {item}: 未获取到版本信息", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)

        setup_list.append(f'ServerModSetup("{item}")')

        new_version = mod_data.get("version")
        title = mod_data.get("title", "")

        typer.secho(
            f"✅ {item} ({title}): {new_version}",
            fg=typer.colors.WHITE,
        )

    typer.secho(
        f"📢 client_mods({len(client_ids)}):",
        fg=typer.colors.GREEN,
    )

    for item in client_ids:
        mod_data = versions.get(item)

        if mod_data is None:
            typer.secho(f"✗  {item}: 未获取到版本信息", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)

        setup_list.append(f'ServerModSetup("{item}")')

        new_version = mod_data.get("version")
        title = mod_data.get("title", "")

        typer.secho(
            f"✅ {item} ({title}): {new_version}",
            fg=typer.colors.WHITE,
        )

    for p in output:
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(setup_list))
        typer.secho(f"💾 <setup_list>已保存到: {p}", fg=typer.colors.CYAN)


if __name__ == "__main__":
    # cmu("d:/github/meme2046/docker/dst/modoverrides.lua", "3486375086")
    convert_update("d:/github/meme2046/docker/dst/modoverrides.lua", "3486375086")
