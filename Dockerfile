FROM python:3.11-slim

# Reduce artefactos innecesarios y mejora observabilidad en logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	FLASK_APP=app.py

WORKDIR /demo

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY apiflaskdemo ./apiflaskdemo
COPY data ./data

RUN addgroup --system app && adduser --system --ingroup app app \
	&& chown -R app:app /demo

# Evita ejecutar la app como root dentro del contenedor.
USER app

EXPOSE 8080

CMD ["flask", "run", "-h", "0.0.0.0", "-p", "8080"]
