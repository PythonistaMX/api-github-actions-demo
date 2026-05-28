# Security

## Controles implementados

### Cadena de suministro

| Control | Herramienta | Dónde |
|---|---|---|
| Análisis de vulnerabilidades en dependencias | Trivy `fs` | `python-app-test.yml` |
| Análisis de configuración del Dockerfile | Trivy config scan | workflows de publicación |
| Análisis de vulnerabilidades en imagen publicada | Trivy image scan (por digest) | workflows de publicación |
| Lint del Dockerfile | Hadolint v2.12.0 | workflows de publicación |
| SBOM (SPDX-JSON) | Syft | workflows de publicación |
| Firma de imagen | Cosign keyless (OIDC) | workflows de publicación |
| Attestation del SBOM | Cosign attest | workflows de publicación |
| Actualizaciones automáticas de dependencias | Dependabot | `.github/dependabot.yml` |

### Imagen Docker

- Base `python:3.14-slim`: superficie mínima de ataque.
- `requirements.runtime.txt` separado de dependencias de desarrollo: las herramientas de test no entran en la imagen de producción.
- Usuario no-root (`app`): el contenedor no corre con privilegios de sistema.
- Binario `uv` copiado desde imagen oficial con versión fijada: reproducibilidad verificable.

### Pipeline CI/CD

- Autenticación a GCP mediante Workload Identity Federation (OIDC): sin llaves estáticas de service account.
- Despliegue blue/green con `--no-traffic`: la revisión candidata se verifica antes de recibir tráfico real.
- Smoke test con identity token de corta duración antes de promover tráfico.
- Rollback automático al nombre exacto de la revisión anterior si el smoke test falla.
- Rama `main` protegida: PRs obligatorios, aprobación requerida, checks de CI como prerequisito.
- `CODEOWNERS` sobre `.github/workflows/`, `pyproject.toml`, `requirements*.txt` y `uv.lock`.

### Quality gates

Todos los workflows de CI ejecutan esta cadena antes de cualquier build o deploy:

```
uv sync --frozen        → reproducibilidad (hashes SHA-256)
ruff check              → lint
ruff format --check     → formato
mypy                    → tipado estático
pytest --cov-fail-under=80  → pruebas + cobertura mínima
```

## Reportar una vulnerabilidad

Abre un *issue* privado o contacta al mantenedor directamente. No publiques detalles de vulnerabilidades en *issues* públicos antes de que se publique un fix.

## Trade-offs conocidos

- El smoke test construye la URL de la revisión candidata con el patrón `https://<tag>---<base>`, que depende de la convención de nombrado actual de Cloud Run. Si Cloud Run cambia el patrón, el test falla sin error de seguridad.
- `ignore-unfixed: true` en Trivy image scan excluye CVEs sin fix disponible para evitar bloqueos en actualizaciones de imagen base. Revisar periódicamente si aparece fix.
