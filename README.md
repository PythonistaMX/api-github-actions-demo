# Aplicación de demostración de una API simple basada en APIFlask

API REST para gestionar un catálogo de alumnos, construida con APIFlask y
SQLAlchemy. Demuestra un pipeline CI/CD completo hacia GCP Cloud Run con
calidad de código, seguridad de imagen y despliegue blue/green.

## Cómo usar este repositorio

**Como referencia de hardening CI/CD** — lee `SECURITY.md` y los archivos
en `.github/workflows/` para ver una implementación real y funcional de:
Workload Identity Federation, Trivy, Cosign, SBOM y despliegue blue/green
con rollback automático. Sin necesidad de clonar ni desplegar.

**Como punto de partida para una API Python con CI/CD** — clona el repo,
adapta los modelos y endpoints en `apiflaskdemo/project/`, ajusta las
variables de entorno y conecta tus propios entornos de GitHub Actions.
La estructura de seguridad del pipeline está resuelta.

**Como submódulo de otro proyecto** — inclúyelo con
`git submodule add <url>` para reutilizar la app o los workflows en otro
contexto sin duplicar código.

## Estructura del proyecto

```
app.py                  # entrypoint: instancia la app y la expone a gunicorn
apiflaskdemo/
  __init__.py           # factory de la app (create_app)
  settings.py           # configuración por entorno (dev/test/prod)
  project/
    models.py           # modelos SQLAlchemy: Alumno, User
    schemas.py          # esquemas de validación APIFlask
    blueprints.py       # endpoints CRUD de alumnos
    auth/               # autenticación HTTP Basic
data/
  alumnos.py            # datos semilla para dev/test
tests/                  # suite pytest
.github/workflows/      # pipelines CI/CD
```

## Desarrollo local

### Requisitos previos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) para gestión de dependencias

### Instalación

```bash
git clone <repo>
cd api-github-actions-demo
uv sync --frozen --extra dev
```

### Ejecutar en modo desarrollo (SQLite en memoria)

```bash
APP_ENV=dev uv run flask run --port 5000
```

El entorno `dev` usa SQLite y carga datos semilla automáticamente al arrancar.

### Ejecutar los tests

```bash
# Tests + cobertura (umbral mínimo: 80%)
uv run pytest --cov=apiflaskdemo --cov-fail-under=80

# Con reporte HTML
uv run pytest --cov=apiflaskdemo --cov-report=html
```

### Lint y formato

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

## Workflows

| Workflow | Trigger | Qué hace |
|---|---|---|
| `python-app-test.yml` | `push main`, `pull_request`, manual | Quality gates (ruff, mypy, pytest-cov, Trivy fs) en matriz Python 3.11/3.12/3.13 |
| `empaqueta.yaml` | Manual | Quality gates → empaquetado con tox → artefacto `.tar.gz` |
| `envia-a-docker.yaml` | Tag `v*.*.*`, manual | Publica imagen en Docker Hub; Trivy, firma Cosign y SBOM en todos los entornos; verificación de firma y attestation solo en `prod` (timeout 2 min) |
| `envia-a-packages.yml` | Tag `v*.*.*`, manual | Publica imagen en GHCR; Trivy, firma Cosign y SBOM en todos los entornos; verificación de firma y attestation solo en `prod` (timeout 2 min) |
| `despliega-cloud-run.yaml` | Tag `v*.*.*`, manual | Despliega en Cloud Run vía OIDC; smoke test + rollback automático |

### Quality gates

Cada workflow de CI ejecuta esta cadena en orden; si un paso falla el pipeline se detiene:

```
uv sync --frozen --extra dev   # instala desde lockfile verificando hashes SHA-256
        ↓
ruff check .                   # lint: errores de estilo y bugs comunes
        ↓
ruff format --check .          # formato: verificación sin modificar archivos
        ↓
mypy .                         # tipado estático
        ↓
pytest --cov=apiflaskdemo \    # pruebas + cobertura mínima del 80%
       --cov-fail-under=80
        ↓
trivy fs (SARIF → GitHub Security)   # vulnerabilidades en dependencias
```

Los resultados de pytest (JUnit XML) y la cobertura (XML) se suben como
artefactos del workflow aunque el pipeline falle, para facilitar el diagnóstico.

## Imagen Docker

La imagen de producción se construye desde `python:3.14-slim` e instala
únicamente las dependencias declaradas en `requirements.runtime.txt`
(6 paquetes: apiflask, email-validator, bcrypt, Flask-SQLAlchemy,
psycopg2-binary, gunicorn) usando `uv pip install --system`. Las dependencias de desarrollo (pytest,
mypy, ruff, etc.) no se incluyen, lo que reduce significativamente la
superficie de vulnerabilidades detectadas por Trivy en el escaneo de imagen.

El binario de `uv` se copia desde la imagen oficial `ghcr.io/astral-sh/uv`
(versión fijada en el Dockerfile) como etapa previa, sin añadir capas de
instalación adicionales.

### Particularidades del registro GHCR (`envia-a-packages.yml`)

GHCR tiene dos diferencias de comportamiento respecto a Docker Hub que afectan
al workflow:

**Nombres de imagen en lowercase obligatorio.** `github.repository` devuelve
el nombre del repositorio con la capitalización original del propietario
(ej. `PythonistaMX/api-github-actions-demo`). `docker/build-push-action`
normaliza a lowercase internamente al publicar, pero cuando el workflow
construye `IMAGE_REF` manualmente para pasarlo a Trivy, Syft y cosign, esa
normalización hay que hacerla de forma explícita:

```bash
IMAGE_NAME_LOWER=$(echo "$IMAGE_NAME" | tr '[:upper:]' '[:lower:]')
```

Sin esto, la librería Go `distribution/reference` que usa Trivy rechaza la
referencia con el error `could not parse image reference` antes de llegar
al escaneo real. Docker Hub no tiene este problema porque `DOCKERHUB_IMAGE`
se construye desde el secreto `DOCKER_USERNAME`, que ya es lowercase.

**Autenticación obligatoria para lectura.** Docker Hub permite pulls públicos
sin credenciales. GHCR requiere autenticación incluso para leer una imagen,
aunque sea pública. El step de Trivy recibe `TRIVY_USERNAME` y
`TRIVY_PASSWORD` (con el `GITHUB_TOKEN` del job) para que pueda descargar
la imagen antes de escanearla.

## Política de tags y releases

Los workflows de publicación (`envia-a-docker`, `envia-a-packages`) se activan automáticamente al crear un git tag semver. El entorno destino se infiere del tag:

| Patrón de tag | Entorno | Ejemplo |
|---|---|---|
| `vX.Y.Z` | `prod` — requiere aprobación | `v1.2.0` |
| `vX.Y.Z-rc.N` | `test` — automático | `v1.2.0-rc.1` |
| `vX.Y.Z-beta.N` | `test` — automático | `v1.2.0-beta.2` |
| `vX.Y.Z-alpha.N` | `test` — automático | `v1.2.0-alpha.1` |

La regla es simple: cualquier tag con `-` va a `test`; sin `-` va a `prod`.

**Flujo recomendado:**

```
git tag v1.2.0-rc.1 && git push --tags   # despliega a test automáticamente
# ... validar en test ...
git tag v1.2.0 && git push --tags         # solicita aprobación → despliega a prod
```

**Gate de aprobación para `prod`:** configura _Required reviewers_ en
`Settings → Environments → prod`. El workflow se pausará antes del job
`push_to_registry` hasta recibir aprobación manual.

**Re-deploys de emergencia:** usa `workflow_dispatch` en el workflow correspondiente
para forzar una imagen existente sin crear un nuevo tag.

### Tags de imagen Docker

Cada publicación genera tres tags de imagen:

| Tag | Descripción |
|---|---|
| `sha-<commit>` | Inmutable — trazabilidad exacta al commit |
| `<version>` | Semver extraído del git tag (ej. `1.2.0`) |
| `latest` | Solo en releases estables (`vX.Y.Z` sin prerelease) |

## Configuración de entornos en GitHub Actions

El proyecto usa tres entornos en `Settings → Environments`: `dev`, `test` y `prod`.
Cada workflow declara `environment: <nombre>` para que GitHub inyecte
automáticamente las variables y secretos del entorno correspondiente.

### Secretos a nivel de repositorio

Se configuran en `Settings → Secrets and variables → Actions → Repository secrets`.
Son compartidos por todos los entornos.

| Secreto | Descripción |
|---|---|
| `DOCKER_USERNAME` | Usuario de Docker Hub para publicar imágenes |
| `DOCKER_PASSWORD` | Token de acceso de Docker Hub (no contraseña) |

> `GITHUB_TOKEN` lo genera GitHub automáticamente; no requiere configuración.

### Entorno `dev` — máquina del desarrollador

Usado por el job `build_artifact` de `empaqueta.yaml`. Usa SQLite como base de
datos, por lo que no requiere servidor ni credenciales de base de datos.

**Variables** (`Settings → Environments → dev → Variables`):

| Variable | Ejemplo |
|---|---|
| `DATABASE_URL` | `sqlite:///apiflask_dev.db` |

**Secretos** (`Settings → Environments → dev → Secrets`):

| Secreto | Descripción |
|---|---|
| `APP_SECRET_KEY` | Clave secreta de Flask |
| `APP_SECURITY_PASSWORD_SALT` | Salt para hashing de contraseñas |

### Entorno `test` — servidor Linux con Docker y PostgreSQL

Usado por `python-app-test.yml`, el job `calidad` de `empaqueta.yaml`,
y los workflows de publicación cuando el tag contiene `-` (prerelease).

**Variables** (`Settings → Environments → test → Variables`):

| Variable | Ejemplo |
|---|---|
| `DATABASE_URL` | `postgresql://user:pass@test-server:5432/apiflask_test` |

**Secretos** (`Settings → Environments → test → Secrets`):

| Secreto | Descripción |
|---|---|
| `APP_SECRET_KEY` | Clave secreta de Flask |
| `APP_SECURITY_PASSWORD_SALT` | Salt para hashing de contraseñas |

### Entorno `prod` — GCP Cloud Run + Cloud SQL

Usado por los workflows de publicación cuando el tag es un release estable
(sin `-`). Configura _Required reviewers_ aquí para el gate de aprobación.

La infraestructura se gestiona con Terraform en `infra/terraform-py271/`.
Los valores de las variables de GCP se obtienen directamente de los outputs de
Terraform tras ejecutar `terraform apply`:

```bash
terraform -chdir=infra/terraform-py271 output
```

**Variables** (`Settings → Environments → prod → Variables`):

| Variable | Origen |
|---|---|
| `GCP_PROJECT_ID` | Valor de `project_id` en `terraform.tfvars` |
| `GCP_REGION` | Valor de `region` en `terraform.tfvars` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `terraform output workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT` | `terraform output cicd_service_account_email` |
| `GCP_CLOUD_RUN_SERVICE` | `terraform output cloud_run_service_name` |
| `GCP_CLOUD_SQL_CONNECTION_NAME` | `terraform output cloud_sql_instance_connection_name` |

> `DATABASE_URL` **no** se configura como variable de GitHub Actions. Terraform
> la inyecta en Cloud Run directamente desde Secret Manager vía
> `value_source.secret_key_ref`. Tras el primer `terraform apply`, pobla la
> versión del secreto manualmente (ver `infra/terraform-py271/README.md`).

Copia `infra/terraform-py271/terraform.tfvars.example` a `terraform.tfvars`
y completa los valores antes de aplicar. La contraseña de base de datos se
pasa como variable de entorno para no escribirla en disco:

```bash
export TF_VAR_db_password="<valor-seguro>"
terraform -chdir=infra/terraform-py271 apply
```

**Secretos** (`Settings → Environments → prod → Secrets`):

| Secreto | Descripción |
|---|---|
| `APP_SECRET_KEY` | Clave secreta de Flask — inyectada en Cloud Run via `--update-secrets` |
| `APP_SECURITY_PASSWORD_SALT` | Salt para hashing de contraseñas — inyectada en Cloud Run via `--update-secrets` |

> **Verificación cosign en `prod`:** los steps `cosign verify` y
> `cosign verify-attestation` consultan Rekor (el log de transparencia de
> Sigstore) y solo se ejecutan en este entorno, justo antes del despliegue.
> Ambos steps tienen `timeout-minutes: 3` y `--timeout 2m` para evitar
> cuelgues si Rekor experimenta latencia alta.

> No guardes JSON keys de service accounts en Secrets. La autenticación con GCP
> se hace vía OIDC Workload Identity Federation; los workflows ya incluyen
> `permissions: id-token: write` para habilitarlo. El binding WIF en
> `iam.tf` restringe el acceso al repositorio y al entorno GitHub Actions
> configurados en `terraform.tfvars`.

## Configuración de rama protegida

La combinación de rama protegida + checks obligatorios + CODEOWNERS sobre workflows
es la base técnica del pipeline de seguridad. Sin ella, las políticas de
revisión son sugerencias que cualquier colaborador con acceso puede ignorar.

Configurar en `Settings → Branches → Add ruleset` sobre la rama `main`:

| Regla | Valor recomendado | Por qué |
|---|---|---|
| Require a pull request before merging | ✅ activado | Ningún cambio llega a `main` sin revisión |
| Required approvals | 1 | Al menos una aprobación humana |
| Require review from Code Owners | ✅ activado | Activa `.github/CODEOWNERS` para archivos críticos |
| Require status checks to pass | ✅ activado | El merge solo ocurre si el CI está verde |
| Required status checks | ver tabla abajo | |
| Block force pushes | ✅ activado | Evita reescribir el historial de `main` |
| Restrict deletions | ✅ activado | Nadie puede borrar la rama principal |

**Status checks requeridos** (nombre exacto tal como aparece en GitHub):

| Check | Workflow | Versiones |
|---|---|---|
| `prueba (3.11)` | `python-app-test.yml` | Python 3.11 |
| `prueba (3.12)` | `python-app-test.yml` | Python 3.12 |
| `prueba (3.13)` | `python-app-test.yml` | Python 3.13 |

### Protección de tags semver

Configurar en `Settings → Rules → New ruleset → Tag` sobre el patrón `v*.*.*`:

| Regla | Por qué |
|---|---|
| Restrict deletions | Un tag de release no puede borrarse retroactivamente |
| Block force pushes | Evita mover el tag a otro commit |

Sin esta protección un tag es una referencia mutable — un vector de ataque
conocido en cadenas de suministro de software.

## Protección de archivos críticos (CODEOWNERS)

`.github/CODEOWNERS` exige aprobación del propietario del repositorio en
cualquier PR que modifique:

| Ruta protegida | Por qué |
|---|---|
| `.github/workflows/` | Evita que un atacante altere el pipeline via PR |
| `pyproject.toml`, `requirements.txt`, `uv.lock` | Previene introducción de dependencias maliciosas |
| `infra/` | Cambios en IaC afectan recursos de producción |

Para activarlo: `Settings → Branches → main → Require review from Code Owners`.

### Variables de entorno en CI

Algunos workflows inyectan variables adicionales que no provienen de GitHub
Environments sino que se fijan directamente en el YAML:

| Variable | Valor en CI | Propósito |
|---|---|---|
| `APP_TESTING` | `"1"` | Activa el modo de prueba en Flask |
| `APP_SEED_DATA` | `"1"` | Carga datos iniciales al arrancar |
| `APP_ENV` | `test` / `prod` | Indica el entorno activo a la app |
x