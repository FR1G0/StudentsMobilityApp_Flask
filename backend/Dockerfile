FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py

EXPOSE 5000

# Run migrations, then serve with gunicorn (production WSGI server).
CMD ["sh", "-c", "flask db upgrade && gunicorn -b 0.0.0.0:5000 -w 4 app:app"]
