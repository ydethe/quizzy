FROM python:3.11-slim

# RUN apt update && apt install -y g++ ca-certificates && update-ca-certificates
# Configure Python to not buffer "stdout" or create .pyc files
ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Add a non-root user for security reasons
RUN adduser --home /app quizzy-user
USER quizzy-user

WORKDIR /app

COPY dist/*.whl .
RUN python -m pip install --no-cache-dir *.whl && rm -f *.whl

# Expose port
EXPOSE 8000

# Run app with gunicorn + uvicorn workers
CMD ["python", "-m", "quizzy"]

HEALTHCHECK --interval=5s --timeout=5s --retries=5 CMD curl --include --request GET http://localhost:8000/health || exit 1
