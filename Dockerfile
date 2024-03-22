FROM python:3.12
WORKDIR /app
ARG SSH_PRIVATE_KEY
RUN mkdir /root/.ssh/ && echo "${SSH_PRIVATE_KEY}" >> /root/.ssh/id_rsa
RUN chmod 400 /root/.ssh/id_rsa && ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN pip install poetry
COPY requirements.txt .
RUN pip install -r requirements.txt --src /usr/local/src

CMD uvicorn app.main:app --reload --host=0.0.0.0
