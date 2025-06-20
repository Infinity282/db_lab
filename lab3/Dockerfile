FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка wait-for-it.sh
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY . .

CMD ["/wait-for-it.sh", "postgres:5432", "--", "/wait-for-it.sh", "neo4j:7687", "--", "/wait-for-it.sh", "redis:6379", "--", "python", "app.py"]