
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import create_router, create_validation_page_router
from app.application.process_calibration import ProcessCalibration
from app.infrastructure.xlsx_reader import XlsxMeasurementReader

app = FastAPI(
    title="Reports Automation API",
    version="0.1.0",
    description="Processa planilhas XLSX de calibracao e retorna resultados metrologicos.",
)

# Permite que o React acesse a API durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    create_router(
        ProcessCalibration(XlsxMeasurementReader())
    )
)


app.include_router(create_validation_page_router())


@app.get("/health", tags=["operacao"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Interface web ja compilada (pasta web/). Usada pelo iniciar_aplicacao_schulz.bat,
# para que a aplicacao rode apenas com Python. Na AWS a pasta nao existe e e ignorada.
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
