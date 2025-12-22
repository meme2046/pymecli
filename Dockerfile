FROM registry.cn-chengdu.aliyuncs.com/jusu/ub24:latest

# 更新包索引并尝试安装 mkcert
RUN brew install mkcert
RUN brew cleanup
RUN mkdir -p /etc/mkcert
RUN uv tool install pymecli -i https://pypi.org/simple
RUN uv tool upgrade --all -i https://pypi.org/simple

# # 复制脚本并赋予权限
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

CMD ["/entrypoint.sh"]