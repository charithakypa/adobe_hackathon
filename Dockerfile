# Use a slim Python image
FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Entry point
CMD ["python", "main.py"]
