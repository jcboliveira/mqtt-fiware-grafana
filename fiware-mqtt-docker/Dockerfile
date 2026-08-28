FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manager.py station_worker.py ./

ENTRYPOINT ["python", "-u", "manager.py"]