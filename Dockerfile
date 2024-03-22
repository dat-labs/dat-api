FROM python:3.10
WORKDIR /app
ARG SSH_PRIVATE_KEY
RUN mkdir /root/.ssh/ && echo "${SSH_PRIVATE_KEY}" >> /root/.ssh/id_rsa
RUN chmod 400 /root/.ssh/id_rsa && ssh-keyscan github.com >> /root/.ssh/known_hosts

COPY pyproject.toml .
COPY poetry.lock .
RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install --no-root
RUN pip install uvicorn[standard]

CMD uvicorn app.main:app --reload --host=0.0.0.0
