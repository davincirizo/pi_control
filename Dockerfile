FROM python:3.13-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=America/Chicago
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --gid 10001 picontrol \
    && useradd --uid 10001 --gid 10001 --no-create-home picontrol \
    && mkdir -p /app/data \
    && chown 10001:10001 /app/data
COPY app.py test_app.py config.example.json ./
COPY templates/ ./templates/
COPY static/ ./static/
USER 10001:10001
RUN python -m unittest -v
CMD ["python", "app.py"]
