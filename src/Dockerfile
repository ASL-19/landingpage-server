FROM python:3.9-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && \
        apt-get install -y postgresql-client-common

WORKDIR /usr/src/app

COPY ./lp_server/requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser
USER 999

COPY ./lp_server/entrypoint.sh /usr/src/app/

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
EXPOSE 8001

COPY ./lp_server/ /usr/src/app/

