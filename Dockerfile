FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# uv export --no-editable --no-emit-project -o requirements.txt > /dev/null
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY src/quizzy .

# Expose port
EXPOSE 8030

# Run app with gunicorn + uvicorn workers
CMD ["python", "main.py"]

# sudo docker build -t quizzy .
# sudo docker run -p 8030:8030 -v ./quizzes:/app/quizzes:ro quizzy
