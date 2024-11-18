FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

ENV MYSQL_ROOT_PASSWORD=mysql_root_password

COPY ./sql/billing_sql.py .

