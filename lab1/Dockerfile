FROM python:3.9-slim

WORKDIR /app

COPY ../db_utils ./db_utils

COPY lab1/app.py .

COPY lab1/utils.py .

COPY lab1/requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
