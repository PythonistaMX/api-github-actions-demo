# Pin por digest SHA: garantiza que el build sea reproducible y que una actualización
# silenciosa del tag 'slim' no introduzca cambios no auditados en la imagen base.
# Para actualizar: docker pull python:3.11-slim && docker inspect --format='{{index .RepoDigests 0}}' python:3.11-slim
# Luego reemplaza el digest y actualiza también la entrada en dependabot.yml (ecosystem: docker).
FROM python:3.11-slim@sha256:ad48727987b259854d52241fac3bc633574364867e5571e796c66bd1be2b0e2b

# Reduce artefactos innecesarios y mejora observabilidad en logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	FLASK_APP=app.py

WORKDIR /demo

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip==24.3.1 \
	&& pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY apiflaskdemo ./apiflaskdemo
COPY data ./data

RUN addgroup --system app && adduser --system --ingroup app app \
	&& chown -R app:app /demo

# Evita ejecutar la app como root dentro del contenedor.
USER app

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
