# Mini-Sprint DevSecOps U3-A4

API académica de laboratorio con Flask y SQLite para ejecución exclusivamente local. Usa datos ficticios.

## Ejecutar en Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python scripts/configurar_demo.py
.\.venv\Scripts\python app.py
```

La aplicación atiende en http://127.0.0.1:5000. Las rutas son GET /api/health, GET /api/profile y POST /api/login. La configuración local se lee desde .env. Git ignora .env y los archivos SQLite.

## Verificación

Con el entorno virtual activo:

```powershell
pre-commit install
pre-commit run --all-files
python -m bandit -r app.py -ll
python -m pip_audit --requirement requirements.txt --no-deps --disable-pip
python -m unittest discover -s tests -v
cyclonedx-py requirements requirements.txt --output-reproducible --validate -o sbom.json
```

El workflow de GitHub Actions ejecuta los escaneos y las pruebas en los pull requests a main, y guarda el SBOM CycloneDX como artefacto.
