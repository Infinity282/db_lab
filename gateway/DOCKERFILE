FROM python:3.9-slim

WORKDIR /app

COPY ./gateway/gateway.py .

COPY ./gateway/const.py .

COPY ./gateway/requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "gateway.py"]
