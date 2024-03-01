FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --src /usr/local/src

CMD uvicorn app.main:app --reload --host=0.0.0.0
