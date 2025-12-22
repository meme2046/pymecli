# build
docker build -t registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest -f Dockerfile .
# tag
docker tag [ImageId] registry.cn-chengdu.aliyuncs.com/jusu/pymecli:[镜像版本号]
# run
(docker run -d 
--name=pymecli
-p 8877:80
registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest)
# push
docker push registry.cn-chengdu.aliyuncs.com/jusu/pymecli:latest