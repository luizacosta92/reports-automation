"""Ponto de entrada da AWS Lambda.

O Lambda nao fala HTTP "puro": ele recebe um evento JSON do API Gateway.
O Mangum e o tradutor que converte esse evento em uma requisicao ASGI
(o padrao que o FastAPI entende) e converte a resposta de volta.
Por isso a API do grupo (app/main.py) roda aqui SEM alterar o arquivo dela.
"""
import os

from mangum import Mangum
from starlette.middleware.cors import CORSMiddleware

from app.main import app

# CORS: quando o site esta em outro endereco que a API (S3 website + API Gateway), o navegador so deixa o site
# chamar a API se ela autorizar essa origem. O template passa o endereco do site em ALLOWED_ORIGIN.
# Com CloudFront (mesma origem) a variavel vem vazia e nada e adicionado.
origem_permitida = os.environ.get("ALLOWED_ORIGIN", "").strip().rstrip("/")
if origem_permitida:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origem_permitida],
        allow_methods=["*"],
        allow_headers=["*"],
    )

# lifespan="off": a API nao usa eventos de startup/shutdown.
handler = Mangum(app, lifespan="off")
