# build
docker build -t registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest -f Dockerfile .
# tag
docker tag [ImageId] registry.cn-chengdu.aliyuncs.com/jusu/pymecli:[镜像版本号]
# run
(docker run -d 
--name=pymecli
-p 8888:80
-e PROXY=socks5://192.168.123.7:7890
registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest)
# push
docker push registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest
# certbot
(docker compose run
--rm certbot certonly
--webroot --webroot-path=/var/www/certbot
-d meme.us.kg
-d www.meme.us.kg)
# certbot dns
(docker run --rm
--name certbot-cloudflare
--rm certbot certonly
-d meme.us.kg
-d www.meme.us.kg
certbot/dns-cloudflare:latest)
# certonly --dns-cloudflare --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini
# --email memeking2046@gmail.com --agree-tos --no-eff-email --force-renewal
# -d meme.us.kg -d www.meme.us.kg
# nginx
docker-compose run nginx
# nginx
(docker run -d
--name=nginx
-v $"(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro"
-v $"(pwd)/certbot/www:/var/www/certbot"
-p 80:80
nginx:latest)
# docker-compose
docker compose -p fast up -d

