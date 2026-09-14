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
etcdsync etcd2mysql /cron/jobs -e d:/.env/pymecli.env -t kvs
etcdsync etcd2mysql "" -e d:/.env/pymecli.env -t kvs # 全量
etcdsync mysql2etcd /cron/jobs -e d:/.env/pymecli.env -t kvs
etcdsync mysql2etcd -e d:/.env/pymecli.env -t kvs # 全量
```
