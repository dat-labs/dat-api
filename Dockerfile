FROM python:3.10
WORKDIR /app

COPY . .
RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry lock && poetry install --no-root
RUN pip install uvicorn[standard]

CMD uvicorn app.main:app --reload --host=0.0.0.0
