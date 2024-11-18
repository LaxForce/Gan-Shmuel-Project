FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

ENV MYSQL_ROOT_PASSWORD=mysql_root_password

RUN mkdir functions
RUN mkdir in
RUN mkdir out
RUN mkdir sql

COPY ./sql/billing_sql.py ./sql
COPY ./sql/__init__.py ./sql
COPY ./functions ./functions
COPY routes.py .
COPY app.py .

CMD ["python", "app.py"]
#CMD ["bash"]
