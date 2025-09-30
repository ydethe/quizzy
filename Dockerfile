FROM python:3.11-slim

# RUN apt update && apt install -y g++ ca-certificates && update-ca-certificates

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dist/*.whl .
RUN python -m pip install --no-cache-dir *.whl && \
    rm -f *.whl

# Expose port
EXPOSE 8030

# Run app with gunicorn + uvicorn workers
CMD ["python", "-m", "quizzy"]

