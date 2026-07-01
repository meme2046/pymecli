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
uv run dst ucm d:/.backups/dontstarvetogether/modoverrides.lua -o c:/.dst/save/Cluster_1/Master/modoverrides.lua -o c:/.dst/save/Cluster_1/Caves/modoverrides.lua
```
