FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY seculeti_ctf /app/seculeti_ctf
COPY front_end-demo /app/front_end-demo

ENV PYTHONPATH=/app
EXPOSE 5000

CMD ["python", "-m", "seculeti_ctf.app.main"]
