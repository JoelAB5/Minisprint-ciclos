"""Genera valores ficticios locales para un entorno de demostración nuevo."""
from pathlib import Path
from secrets import token_urlsafe

path = Path(__file__).resolve().parents[1] / ".env"
try:
    with path.open("x", encoding="utf-8") as env_file:
        env_file.write(f"PRACTICA_API_KEY={token_urlsafe(24)}\n")
        env_file.write(f"PRACTICA_DEMO_PASSWORD={token_urlsafe(16)}\n")
except FileExistsError:
    print("Ya existe .env. Se conservó su contenido.")
else:
    print(".env creado para la demostración. Git lo ignora.")
