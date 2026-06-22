# টার্মিনালে এই কমান্ড দিন:
cat > Dockerfile << 'EOF'
FROM python:3-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8000", "--timeout", "120", "--workers", "1", "--threads", "2"]
EOF
