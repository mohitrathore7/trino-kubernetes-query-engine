FROM python:3.12-slim

WORKDIR /app
COPY python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY python/tqe ./tqe
COPY queries ./queries

ENTRYPOINT ["python", "-m", "tqe"]
CMD ["all"]
