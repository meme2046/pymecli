FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# 更新包索引并尝试安装 mkcert
RUN apt-get update && apt-get install -y mkcert && apt clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/mkcert
RUN uv tool install pymecli -i https://pypi.org/simple
RUN uv tool upgrade --all -i https://pypi.org/simple

# # 复制脚本并赋予权限
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

CMD ["/entrypoint.sh"]