# Use the official Python image as the base image
FROM python:3.13.0

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port 8000
EXPOSE 8000

# Start the FastAPI server
CMD ["ENV=production", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]