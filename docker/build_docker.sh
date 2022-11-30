DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
docker build -f $DIR/Dockerfile_updated -t pederbg/fram .
