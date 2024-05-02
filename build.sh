NAME=${PWD##*/}
REV_TAG=$(git log -1 --pretty=format:%h)
IMAGE=$NAME:$REV_TAG

docker ps -q --filter "name=$NAME" \
    | grep -q . \
    && docker rm -f $NAME 1> /dev/null
docker build -t $IMAGE .
docker run --name $NAME -d $IMAGE
