"""Copia o codigo da API (app/) para infra/api_src/ antes do `sam build`.

Por que isso existe: o SAM empacota apenas a pasta indicada em CodeUri.
Em vez de empacotar o repositorio inteiro (frontend, testes, node_modules),
copiamos so a pasta `app/` do back-end para dentro de api_src/.

Uso (a partir da raiz do repositorio):  python infra/prepare.py
"""
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "app"
DESTINO = RAIZ / "infra" / "api_src" / "app"

if not (ORIGEM / "main.py").exists():
    raise SystemExit(f"Nao encontrei {ORIGEM / 'main.py'}. Rode a partir do repositorio reports-automation.")

if DESTINO.exists():
    shutil.rmtree(DESTINO)
shutil.copytree(ORIGEM, DESTINO, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
print(f"Codigo copiado: {ORIGEM} -> {DESTINO}")
