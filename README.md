# pymecli

个人 CLI 工具集，基于 [Typer](https://typer.tiangolo.com/) 构建，包含 FastAPI 服务、Redis/MySQL/Etcd 数据同步、DDNS、加密货币行情等模块。

## 快速开始

```shell
# pipx install pymecli # 使用pipx安装
uv tool install pymecli # 使用uv安装
uv tool list
uv run util --help  # 查看所有工具命令
```

## 开发
```shell
uv sync            # 安装依赖
uv run util --help  # 查看所有工具命令
uv build                      # 打包
uv publish --token <TOKEN>    # 发布到 PyPI
```

## 模块一览

| 命令 | 文件 | 说明 |
|---|---|---|
| `util` | `cli/util.py` | 通用工具（ID 生成、时间、emoji、IPv6 等） |
| `example` | `cli/example.py` | Typer 示例 |
| `fast` | `cli/fast.py` | FastAPI 服务（clash 订阅转换、Redis API） |
| `dst` | `cli/dst.py` | 饥荒专服模组管理 |
| `etcdsync` | `cli/etcd_sync.py` | MySQL ↔ Etcd 数据同步 |
| `quark` | `cli/quark.py` | 夸克网盘自动签到 |
| `dnspod` | `cli/dnspod.py` | DNSPod DDNS 自动更新 |
| `bitget` | `cli/bitget.py` | Bitget 行情 + grid 同步 |
| `gate` | `cli/gate.py` | Gate grid 数据同步 |
| `okx` | `cli/okx.py` | OKX grid 数据同步 |
| `rd` | `cli/redis_csv.py` | Redis ↔ CSV 数据处理 |
| `tele` | `cli/tele.py` | Telegram 工具 |

---

## util — 通用工具

```shell
# 生成 secure_id（默认 30 位，字母开头，剔除 i I l L o O 0 1）
uv run util sid              # 默认 30 位
uv run util sid 16           # 指定长度 16

# 生成 UUID / 打印系统信息
uv run util uuid             # 输出 uuid4()
uv run util os               # Windows / Darwin / Linux

# 时间戳（秒 / 毫秒）
uv run util ts               # 当前秒级时间戳
uv run util ms               # 当前毫秒级时间戳

# Python 版本 / 时区时间 / emoji
uv run util v                # 打印 Python 版本
uv run util st               # 同时打印 UTC / 美东 / 上海时间
uv run util emoji            # 表格形式打印常用 emoji

# Uniswap token 排序
uv run util stoken 0xC02aaA... 0xA0b869...   # 返回 token0 token1（按数值排序）

# 获取本地 IPv6 稳定地址
uv run util ipv6             # 打印并写入 Redis key: local.IPv6
```

## example — Typer 示例

```shell
uv run example hello Xiaoming
uv run example hello Xiaoming --from Pymecli
uv run example goodbye Xiaoming
uv run example goodbye Xiaoming -f
```

## fast — FastAPI 服务

```shell
uv run fast --port 8877      # 启动本地服务
```

## dst — 饥荒专服模组

```shell
# 更新 modoverrides.lua 中指定模组的版本信息
uv run dst convert-update d:/.backups/dontstarvetogether/modoverrides.lua \
    -o c:/.dst/save/Cluster_1/Master/modoverrides.lua \
    -o c:/.dst/save/Cluster_1/Caves/modoverrides.lua

# 列出所有 mod，生成 dedicated_server_mods_setup.lua
uv run dst mod-setup d:/.backups/dontstarvetogether/modoverrides.lua \
    -m 3486375086
```

## etcdsync — MySQL ↔ Etcd 同步

```shell
# MySQL → Etcd
uv run etcdsync mysql2etcd /test -e d:/.env/pymecli.env -t kvs
uv run etcdsync mysql2etcd ""    -e d:/.env/pymecli.env -t kvs   # 全量

# Etcd → MySQL
uv run etcdsync etcd2mysql /test -e d:/.env/pymecli.env -t kvs
uv run etcdsync etcd2mysql ""    -e d:/.env/pymecli.env -t kvs   # 全量

# Etcd → JSON / JSON → Etcd
uv run etcdsync etcd2json /test -e d:/.env/pymecli.env -f xxx.json
uv run etcdsync json2etcd /test -e d:/.env/pymecli.env -f xxx.json
```

## quark — 夸克网盘签到

```shell
uv run quark sign                    # 签到（默认发通知）
uv run quark sign --no-notify        # 签到但不发通知
uv run quark sign -e /path/to/.env   # 指定 dotenv 路径
uv run quark check                   # 检查账号配置和成长信息
```

## dnspod — DDNS

### 环境变量

- `DP_ID`: DNSPod 登录 ID
- `DP_TOKEN`: DNSPod 登录 Token
- `DP_DOMAIN`: 域名（如 cursor.email）
- `DP_RECORD_ID`: IPv4 A 记录 ID
- `DP_RECORD_ID_IPV6`: IPv6 AAAA 记录 ID
- `DP_SUB_DOMAIN`: 子域名前缀（默认 "api"）
- `DP_RECORD_LINE`: 记录线路（默认 "默认"）

### 示例

```shell
uv run dnspod list          # 列出域名下所有记录（先跑这个查 record_id）
uv run dnspod ddns          # 更新 IPv4 A 记录
uv run dnspod ddns --force  # 强制更新（即使 IP 没变化）
uv run dnspod ddns6         # 更新 IPv6 AAAA 记录（从 Redis 读 local.IPv6）
uv run dnspod ddns6 --force
```

## bitget — Bitget 行情

```shell
# 同步 MySQL grid 数据到 Redis
uv run bitget sync d:/.env/pymecli.env

# 获取现货 / 合约价格（支持代理）
uv run bitget spot BTCUSDT,ETHUSDT
uv run bitget spot BTCUSDT -p http://127.0.0.1:7897
uv run bitget mix  BTCUSDT_UMCBL,SOLUSDT_UMCBL -p http://127.0.0.1:7897
```

## gate / okx — Grid 数据同步

```shell
uv run gate d:/.env/pymecli.env    # Gate → Redis
uv run okx  d:/.env/pymecli.env    # OKX → Redis
```

## rd — Redis ↔ CSV

```shell
# 查询 Redis ZSet 记录数
uv run rd count my_prefix

# CSV → Redis（按 id1、id2 组合 key）
uv run rd csv2redis symbol timeframe -fp data/file.csv -kp my_prefix

# CSV → CSV（时间字符串转时间戳、删列）
uv run rd convert data/file.csv
```

## tele — Telegram 工具

> 需先在 `pyproject.toml` 的 `[project.scripts]` 取消注释 `tele = "cli.tele:app"`。

```shell
uv run tele info .env              # 查看 TELE_SESSION_STRING
uv run tele check .env             # 验证 session 是否有效
uv run tele login .env             # 登录生成新 session
uv run tele upload image.jpg       # 上传图片到 Telegram
uv run tele list-channels .env     # 列出已加入的频道
```
