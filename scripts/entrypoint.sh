#!/bin/bash

# if [ ! -f "/etc/mkcert/key.pem" ] || [ ! -f "/etc/mkcert/cert.pem" ]; then
#     rm -rf /etc/mkcert/*
#     # 初始化本地证书颁发机构（CA）​
#     mkcert -install
#     # 生成证书
#     mkcert -cert-file /etc/mkcert/cert.pem \
#       -key-file /etc/mkcert/key.pem \
#       localhost 127.0.0.1 ::1 192.168.123.7 meme.us.kg www.meme.us.kg
# fi
# windows 下生成证书⬇️⬇️⬇️
# mkcert -cert-file d:/.ssh/mkcert/cert.pem -key-file d:/.ssh/mkcert/key.pem localhost 127.0.0.1 ::1 192.168.123.7

# 添加代理参数支持
PROXY_ARG=""
if [ -n "$PROXY" ]; then # -n: non-empty
    PROXY_ARG="--proxy $PROXY"
fi

# --ssl-keyfile /etc/mkcert/key.pem \
# --ssl-certfile /etc/mkcert/cert.pem \

# 启动 FastAPI 服务
eval "fast 0.0.0.0 --port 80 \
  --rule https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release \
  --my-rule https://raw.githubusercontent.com/meme2046/data/refs/heads/main/clash \
  $PROXY_ARG"