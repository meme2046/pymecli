import re
from typing import Dict, List, Optional

import requests
import typer
from slpp import slpp as lua

app = typer.Typer()

STEAM_API_URL = (
    "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v0001"
)


def get_mod_versions(workshop_ids: List[str]) -> Dict[str, Optional[str]]:
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
        typer.secho(f"❌ Steam API 请求失败: {e}", fg=typer.colors.RED)
        return {}

    versions: Dict[str, Optional[str]] = {}
    for detail in result["response"].get("publishedfiledetails", []):
        publishedfileid = detail.get("publishedfileid")
        tags = detail.get("tags", [])
        version = None
        for tag in tags:
            tag_str = tag.get("tag", "")
            if tag_str.startswith("version:"):
                version = tag_str.replace("version:", "")
                break
        versions[publishedfileid] = version

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


def get_client_mods_list(file_path: str, mod_id: str) -> Optional[tuple[dict, dict]]:
    """
    解析 lua 文件，返回 (data, client_mods_list)。
    失败返回 None（错误信息已由函数自行打印）。
    """
    try:
        data = parse_lua_file(file_path)
    except FileNotFoundError:
        typer.secho(f"❌ 文件不存在: {file_path}", fg=typer.colors.RED)
        return None
    except Exception as e:
        typer.secho(f"❌ 解析 Lua 文件失败: {e}", fg=typer.colors.RED)
        return None

    main_mod_key = f"workshop-{mod_id}"
    main_mod = data.get(main_mod_key)
    if not main_mod:
        typer.secho(f"❌ 未找到 {main_mod_key}", fg=typer.colors.RED)
        return None

    client_mods_list = main_mod.get("configuration_options", {}).get(
        "client_mods_list", {}
    )
    if not client_mods_list:
        typer.secho("❌ 未找到 client_mods_list", fg=typer.colors.RED)
        return None

    return data, client_mods_list


# update_client_mods
@app.command()
def ucm(
    file_path: str = typer.Argument(
        "d:/.backups/dontstarvetogether/modoverrides.lua",
        help="modoverrides.lua 文件路径",
    ),
    mod_id: str = typer.Option(
        "3486375086",
        "--mod-id",
        "-m",
        help="主 mod 的 workshop ID",
    ),
    output: List[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="额外的输出路径，可多次指定",
    ),
):
    result = get_client_mods_list(file_path, mod_id)
    if result is None:
        raise typer.Exit(code=1)
    data, client_mods_list = result

    workshop_ids = []
    for key in client_mods_list.keys():
        wid = extract_workshop_id(key)
        if wid:
            workshop_ids.append(wid)

    if not workshop_ids:
        typer.secho("❌ 未找到任何 client_mods", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(
        f"🔍 发现 {len(workshop_ids)} 个 client mods，正在查询 Steam API...",
        fg=typer.colors.BLUE,
    )
    versions = get_mod_versions(workshop_ids)

    if not versions:
        typer.secho("❌ 未能获取版本信息", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho("📝 正在更新版本号...", fg=typer.colors.BLUE)
    updated_count = 0
    for mod_key, mod_info in client_mods_list.items():
        wid = extract_workshop_id(mod_key)
        if not wid:
            continue
        new_version = versions.get(wid)
        if new_version is None:
            typer.secho(f"⚠️  {mod_key}: 未获取到版本信息", fg=typer.colors.YELLOW)
            continue
        old_version = mod_info.get("version")
        if old_version != new_version:
            mod_info["version"] = new_version
            updated_count += 1
            typer.secho(
                f"✅ {mod_key}: {old_version} -> {new_version}",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho(
                f"ℹ️  {mod_key}: 已是最新版本 {old_version}",
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
        typer.secho(f"❌ 写入文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if updated_count > 0:
        typer.secho(f"\n🎉 成功更新 {updated_count} 个 mod 版本", fg=typer.colors.GREEN)
    else:
        typer.secho("\nℹ️  所有 mod 已是最新版本", fg=typer.colors.YELLOW)


@app.command()
def lst(
    file_path: str = typer.Argument(
        "d:/.backups/dontstarvetogether/modoverrides.lua",
        help="modoverrides.lua 文件路径",
    ),
    mod_id: str = typer.Option(
        "3486375086",
        "--mod-id",
        "-m",
        help="主 mod 的 workshop ID",
    ),
):
    """
    列出 client_mods_list 中所有 mod 的当前版本
    """
    result = get_client_mods_list(file_path, mod_id)
    if result is None:
        raise typer.Exit(code=1)
    _, client_mods_list = result

    typer.secho("\n📋 client_mods_list 中的 mod 列表:\n", fg=typer.colors.BLUE)
    for mod_key, mod_info in client_mods_list.items():
        version = mod_info.get("version", "unknown")
        typer.secho(f"  {mod_key}: {version}", fg=typer.colors.WHITE)


if __name__ == "__main__":
    # ucm("d:/.backups/dontstarvetogether/modoverrides.lua", "3486375086")
    lst("d:/.backups/dontstarvetogether/modoverrides.lua", "3486375086")
