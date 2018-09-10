DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
docker build -f $DIR/Dockerfile -t pederbg/fram19 .
