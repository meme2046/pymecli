# build
docker build -t registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest -f Dockerfile .
# tag
docker tag [ImageId] registry.cn-chengdu.aliyuncs.com/jusu/pymecli:[镜像版本号]
# run
(docker run -d 
--name=pymecli
-p 8877:443
-v d:/.ssh/mkcert:/etc/mkcert
registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest)
# push
docker push registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest