# Base image
FROM python:3.10-slim

# Install mysql-client
RUN apt-get update && apt-get install -y default-mysql-client

# Set app container working directory
WORKDIR /app

# Copy requirement dependencies txt to the /app container directory
COPY requirements.txt /app/

# Install the dependencies listed in requirements.txt using pip
RUN pip install -r requirements.txt

# Copy necessary files to the /app container directory
COPY weight_app.py .env /app/

# Set environment variable to specify the Flask app file
ENV FLASK_APP=weight_app.py

# Define the default command to run the application (Flask app) when the container starts
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
