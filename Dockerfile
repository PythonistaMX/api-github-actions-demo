# Usamos tag versionado para evitar roturas por digests retirados y mantener
# una base estable en la rama 3.11.
FROM python:3.11-slim

# Instala el binario de uv para gestionar dependencias de forma reproducible.
COPY --from=ghcr.io/astral-sh/uv:0.7.22 /uv /uvx /bin/

# Reduce artefactos innecesarios y mejora observabilidad en logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	FLASK_APP=app.py

WORKDIR /demo

COPY requirements.runtime.txt ./
RUN uv pip install --system --no-cache --upgrade "setuptools>=80.0.0" "wheel>=0.46.2" \
	&& uv pip install --system --no-cache -r requirements.runtime.txt

COPY app.py ./
COPY apiflaskdemo ./apiflaskdemo
COPY data ./data

RUN addgroup --system app && adduser --system --ingroup app app \
	&& chown -R app:app /demo

# Evita ejecutar la app como root dentro del contenedor.
USER app

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
