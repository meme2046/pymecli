FROM registry.cn-chengdu.aliyuncs.com/jusu/ub24:latest

# https://pypi.org/simple
# https://mirrors.cloud.tencent.com/pypi/simple
RUN uv tool install pymecli -i https://mirrors.cloud.tencent.com/pypi/simple
RUN uv tool upgrade --all -i https://mirrors.cloud.tencent.com/pypi/simple

# # 复制脚本并赋予权限
COPY ./scripts/entrypoint.sh /files/entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

CMD ["/files/entrypoint.sh"]
