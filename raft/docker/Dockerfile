FROM --platform=linux/amd64 busybox:1.34.1 as source
FROM --platform=linux/amd64 adoptopenjdk/openjdk8

COPY --from=source /bin/sh /bin/sh
COPY --from=source /bin/mkdir /bin/mkdir

COPY * /app
WORKDIR /app

CMD ["bash", "-c"]
ENTRYPOINT ["bash", "-c"]

