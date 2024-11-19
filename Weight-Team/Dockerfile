# Base image
FROM python:3.10-slim

# Install mysql-client and other dependencies
RUN apt-get update && apt-get install -y default-mysql-client && apt-get clean

# Set app container working directory
WORKDIR /app

# Copy requirement dependencies txt to the /app container directory
COPY requirements.txt /app/

# Install the dependencies listed in requirements.txt using pip
RUN pip install -r requirements.txt

# Copy necessary files to the /app container directory
COPY weight_app.py .env /app/
COPY weight_db/trucks.json /app/trucks.json

# Set environment variable to specify the Flask app file
ENV FLASK_APP=weight_app.py

# Default command for the container
CMD ["flask", "run", "--host=0.0.0.0", "--port=5002"]