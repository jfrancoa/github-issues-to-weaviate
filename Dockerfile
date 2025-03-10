FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./

# Make the script executable
RUN chmod +x /app/main.py

# Set the entrypoint
ENTRYPOINT ["python", "/app/main.py"]

