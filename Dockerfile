FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim
RUN apt update
# RUN apt install -y mkcert  
RUN apt install -y libopencv-dev

RUN apt clean
RUN rm -rf /var/lib/apt/lists/*
# RUN mkdir -p /etc/mkcert

RUN uv python list
RUN uv python install cpython-3.10.19-linux-x86_64-gnu
RUN uv python pin cpython-3.10.19-linux-x86_64-gnu
# https://pypi.org/simple
# https://mirrors.cloud.tencent.com/pypi/simple
RUN uv tool install pymecli -i https://mirrors.cloud.tencent.com/pypi/simple
RUN uv tool upgrade --all -i https://mirrors.cloud.tencent.com/pypi/simple

# # 复制脚本并赋予权限
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

CMD ["/entrypoint.sh"]