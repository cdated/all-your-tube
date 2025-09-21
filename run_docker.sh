docker run --rm \
    --user $(id -u):$(id -g) \
    --name all-your-tube \
    -p 1425:1424 \
    -v $(pwd)/downloads:/tmp/downloads \
    -v $(pwd)/cookie:/tmp/cookie \
    -e AYT_YTDLP_COOKIE="--cookies /tmp/cookie" \
    all-your-tube
