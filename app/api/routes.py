import os
from html import escape

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from app.application.certificate_token import issue_certificate, verify_token
from app.application.process_calibration import ProcessCalibration
from app.infrastructure.certificate_pdf import build_certificate_pdf


def _public_base_url(request: Request) -> str:
    """Endereco usado dentro do QR Code. Em producao, defina PUBLIC_BASE_URL."""
    configured = os.environ.get("PUBLIC_BASE_URL", "").strip()
    return (configured or str(request.base_url)).rstrip("/")


def create_router(process_calibration: ProcessCalibration) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["calibracoes"])

    @router.post("/calibrations/process")
    async def process_calibration_file(file: UploadFile = File(...)) -> dict:
        if not file.filename or not file.filename.lower().endswith(".xlsx"):
            raise HTTPException(status_code=415, detail="Envie somente arquivos .xlsx.")
        try:
            return process_calibration.execute(await file.read())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.post("/calibrations/certificate")
    async def issue_certificate_pdf(request: Request, file: UploadFile = File(...)) -> Response:
        if not file.filename or not file.filename.lower().endswith(".xlsx"):
            raise HTTPException(status_code=415, detail="Envie somente arquivos .xlsx.")
        try:
            result = process_calibration.execute(await file.read())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        certificate = issue_certificate(result)
        url = f"{_public_base_url(request)}/validar?t={certificate['token']}"
        pdf = build_certificate_pdf(result, certificate, url)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{certificate["id"]}.pdf"'},
        )

    @router.get("/certificates/validate")
    def validate_certificate(t: str) -> dict:
        payload = verify_token(t)
        if payload is None:
            raise HTTPException(status_code=404, detail="Certificado inválido ou adulterado.")
        return {"valido": True, **payload}

    return router


def create_validation_page_router() -> APIRouter:
    """Pagina aberta pelo celular ao ler o QR Code (sem prefixo /api)."""
    router = APIRouter(tags=["validacao"])

    @router.get("/validar", response_class=HTMLResponse)
    def validation_page(t: str = "") -> HTMLResponse:
        payload = verify_token(t) if t else None
        return HTMLResponse(_render_validation_page(payload), status_code=200 if payload else 404)

    return router


def _render_validation_page(payload: dict | None) -> str:
    style = (
        "body{font-family:Arial,sans-serif;margin:0;background:#f5f8fb;color:#1f2d3d}"
        "main{max-width:460px;margin:0 auto;padding:24px 18px}"
        ".card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.08)}"
        "h1{font-size:18px;margin:0 0 14px;color:#1c5f98}"
        ".status{font-size:20px;font-weight:700;margin-bottom:12px}"
        ".ok{color:#1f8f5a}.bad{color:#c0392b}"
        "dt{font-size:12px;color:#61758a;margin-top:10px}dd{margin:2px 0 0;font-size:15px}"
    )
    if payload is None:
        body = (
            '<div class="status bad">Certificado inválido</div>'
            "<p>Não foi possível confirmar este certificado. O QR Code pode estar incompleto "
            "ou os dados podem ter sido alterados.</p>"
        )
    else:
        verdict_class = "ok" if payload.get("p") == "APROVADO" else "bad"
        rows = [
            ("Certificado", payload.get("id", "")),
            ("Emitido em (UTC)", str(payload.get("em", "")).replace("T", " ")[:19]),
            ("Cliente", payload.get("c", "")),
            ("Técnico", payload.get("t", "")),
            ("Pontos avaliados", str(payload.get("n", ""))),
            ("Pontos fora da tolerância", str(payload.get("f", ""))),
        ]
        items = "".join(f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>" for k, v in rows)
        body = (
            '<div class="status ok">Certificado autêntico</div>'
            f'<div class="status {verdict_class}">Parecer: {escape(str(payload.get("p", "")))}</div>'
            f"<dl>{items}</dl>"
        )
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Validação de certificado</title><style>{style}</style></head>"
        f'<body><main><div class="card"><h1>Validação de certificado - Schulz S.A.</h1>{body}</div></main></body></html>'
    )