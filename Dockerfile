FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py schema.sql seed.py ./

RUN python -c "import sqlite3; sqlite3.connect('securenotes.db').executescript(open('schema.sql').read())" && python seed.py

RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
