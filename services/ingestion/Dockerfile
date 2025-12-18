# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies in a single layer for optimization
# Use Torch CPU to keep the image size manageable
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 \
    torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Command to run the application
CMD ["python", "main.py"]