# Use the official Python image as base
FROM python:3.9-slim

# Set a working directory in the container
WORKDIR /app

# Copy requirements.txt first (we'll create it next)
COPY requirements.txt .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app's source code to the container
COPY . .

# Expose port 8080 for the Flask app
EXPOSE 8080

# Command to run the Flask app
CMD ["python", "app.py"]
