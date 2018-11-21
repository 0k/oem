
FROM python:2-alpine3.7 as common

CMD ["/bin/sh"]

RUN apk --no-cache --update add libxml2-utils libxslt zlib libxml2 git


FROM common as builder

RUN apk add python-dev build-base libxslt-dev zlib-dev libxml2-dev

COPY . /tmp/src

RUN cd /tmp/src && \
    ./autogen.sh && \
    pip install -r requirements.txt && \
    python setup.py install


FROM common

COPY --from=builder /usr/local /usr/local

CMD ["/usr/local/bin/oem"]