# typer example

```shell
uv run example hello Xiaoming
uv run example hello Xiaoming --from Pymecli
uv run example goodbye Xiaoming
uv run example goodbye Xiaoming -f
```

# fastapi server

```shell
uv run fast --port 8877 # local server
uv build
uv publish --token < TOKEN > # publish
```

# dontstarvetogether

1. 饥荒专服禁client mods使用, 更新client mods version, modoverrides.lua:

```shell
uv run dst cmu d:/.backups/dontstarvetogether/modoverrides.lua -o c:/.dst/save/Cluster_1/Master/modoverrides.lua -o c:/.dst/save/Cluster_1/Caves/modoverrides.lua

uv run dst cml d:/.backups/dontstarvetogether/modoverrides.lua -m 3486375086
```

# etcdsync

```shell
etcdsync etcd2mysql /test -e d:/.env/pymecli.env -t kvs
etcdsync etcd2mysql "" -e d:/.env/pymecli.env -t kvs # 全量
etcdsync mysql2etcd /test -e d:/.env/pymecli.env -t kvs
etcdsync mysql2etcd -e d:/.env/pymecli.env -t kvs # 全量

etcdsync etcd2json  /test -e d:/.env/pymecli.env -f xxx.json
etcdsync json2etcd  /test -e d:/.env/pymecli.env -f xxx.json
```
# quark
```shell
# 执行签到（默认会发通知）
uv run quark sign
# 签到但不发通知
uv run quark sign --no-notify
# 指定不同的 dotenv 路径
uv run quark sign -e /path/to/.env
# 只检查账号状态（不签到），方便调试
uv run quark check
```

# dnspod
## 环境变量说明
- `DP_ID`:         DNSPod 登录 ID
- `DP_TOKEN`:      DNSPod 登录 Token
- `DP_DOMAIN`:     域名 (如 cursor.email)
- `DP_RECORD_ID`:  IPv4 A 记录 ID
- `DP_RECORD_ID_IPV6`: IPv6 AAAA 记录 ID
- `DP_SUB_DOMAIN`: 子域名前缀 (默认 "api")
- `DP_RECORD_LINE`: 记录线路 (默认 "默认")
## 示例
```shell
# 列出域名下所有记录（先跑这个查 record_id）
uv run dnspod list
# 更新 IPv4 A 记录
uv run dnspod ddns
# 强制更新（即使 IP 没变化）
uv run dnspod ddns --force
# 更新 IPv6 AAAA 记录（从 Redis 读 local.IPv6）
uv run dnspod ddns6
uv run dnspod ddns6 --force
```