FROM python:3-slim

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y default-mysql-client expect bash rsync ssh

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

COPY src/ /app/src/
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]