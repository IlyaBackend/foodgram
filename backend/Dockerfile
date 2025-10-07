FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 7000

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:7000", "backend.wsgi"]