#!/bin/bash

if [ ! -f "/etc/mkcert/key.pem" ] || [ ! -f "/etc/mkcert/cert.pem" ]; then
    rm -rf /etc/mkcert/*
    # 初始化本地证书颁发机构（CA）​
    mkcert -install
    # 生成证书
    mkcert -cert-file /etc/mkcert/cert.pem \
      -key-file /etc/mkcert/key.pem \
      example.com localhost 127.0.0.1 ::1 192.168.123.7 meme.us.kg
fi
# windows 下生成证书⬇️⬇️⬇️
# mkcert -cert-file d:/.ssh/mkcert/cert.pem -key-file d:/.ssh/mkcert/key.pem example.com localhost 127.0.0.1 ::1 192.168.123.7

# 启动 FastAPI 服务
fast --port 80 \
  --proxy socks5://192.168.123.7:7890 \
  --ssl-keyfile /etc/mkcert/key.pem \
  --ssl-certfile /etc/mkcert/cert.pem