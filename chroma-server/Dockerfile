# Use a Python 3.10 base image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the dependencies from requirements.txt using pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Set the CMD to run the application using Gunicorn with 4 workers
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "app:app"]
