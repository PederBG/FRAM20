DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
docker run --net=host -it --privileged -v $(realpath $DIR/..):/root/fram --name FRAM --rm pederbg/fram:latest
