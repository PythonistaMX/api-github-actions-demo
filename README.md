# Aplicación de demostración de una API simple basada en APiFlask

## Configuración de entornos en GitHub Actions

Este proyecto espera tres entornos en GitHub Actions: `dev`, `test` y `prod`.

Variables por entorno (`Settings` -> `Environments` -> `Variables`):

- `DATABASE_URL`: cadena de conexión de base de datos por entorno.

Secretos por entorno (`Settings` -> `Environments` -> `Secrets`):

- `APP_SECRET_KEY`: clave secreta de la aplicación.
- `APP_SECURITY_PASSWORD_SALT`: salt para funciones de seguridad.

Notas operativas:

- La app toma configuración desde variables de entorno en `apiflaskdemo/settings.py`.
- Los workflows usan `environment` para consumir `vars` y `secrets` del entorno seleccionado.
- Para pruebas automatizadas se usa `APP_TESTING=1` y `APP_SEED_DATA=1` en CI.

## Integración con Terraform y OIDC en GCP

Para `prod`, el flujo recomendado es:

1. Terraform aprovisiona infraestructura en `infra/terraform-py271`.
2. GitHub Actions autentica con OIDC (sin llaves estáticas).
3. El pipeline usa variables de entorno y outputs de Terraform para desplegar.

Variables recomendadas en el entorno `prod`:

- `GCP_PROJECT_ID`: ID del proyecto GCP.
- `GCP_REGION`: región de despliegue.
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: recurso WIF, por ejemplo `projects/.../providers/...`.
- `GCP_SERVICE_ACCOUNT`: cuenta de servicio para despliegue, por ejemplo `cicd-deployer@...`.
- `DATABASE_URL`: cadena de conexión a Cloud SQL PostgreSQL.

Secretos recomendados en el entorno `prod`:

- `APP_SECRET_KEY`
- `APP_SECURITY_PASSWORD_SALT`

Notas de seguridad:

- Evita guardar JSON keys de service accounts en GitHub Secrets.
- Usa `permissions: id-token: write` en jobs que autentican contra GCP.
- Protege el entorno `prod` con aprobaciones y ramas permitidas.
