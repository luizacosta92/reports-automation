from io import BytesIO
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.application.certificate_token import issue_certificate, verify_token
from app.main import app


client = TestClient(app)


def _xlsx(readings=(10.1, 10.3)) -> dict:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Cliente", "Schulz S.A."])
    sheet.append(["Tecnico Executante", "Maria"])
    sheet.append([])
    sheet.append(["Parametro", "Nominal", "Tol +", "Tol -", "Medida 1", "Medida 2"])
    sheet.append(["P1", 10, 0.2, -0.2, *readings])
    buffer = BytesIO()
    workbook.save(buffer)
    return {"file": ("calibracao.xlsx", buffer.getvalue(), "application/octet-stream")}


def test_certificate_endpoint_returns_pdf():
    response = client.post("/api/v1/calibrations/certificate", files=_xlsx())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "CERT-" in response.headers["content-disposition"]


def test_certificate_rejects_non_xlsx():
    response = client.post(
        "/api/v1/calibrations/certificate",
        files={"file": ("dados.txt", b"x", "text/plain")},
    )

    assert response.status_code == 415


def test_token_is_valid_and_detects_tampering():
    result = client.post("/api/v1/calibrations/process", files=_xlsx()).json()
    certificate = issue_certificate(result)

    payload = verify_token(certificate["token"])
    assert payload["id"] == certificate["id"]
    assert payload["p"] == "APROVADO"

    body, signature = certificate["token"].split(".")
    forged = body[:-2] + ("AA" if not body.endswith("AA") else "BB") + "." + signature
    assert verify_token(forged) is None
    assert verify_token("lixo") is None


def test_validation_page_and_api():
    result = client.post("/api/v1/calibrations/process", files=_xlsx((10.5, 10.6))).json()
    token = issue_certificate(result)["token"]

    page = client.get("/validar", params={"t": token})
    assert page.status_code == 200
    assert "Certificado autêntico" in page.text
    assert "REPROVADO" in page.text

    api = client.get("/api/v1/certificates/validate", params={"t": token})
    assert api.status_code == 200
    assert api.json()["valido"] is True
    assert api.json()["f"] == 1

    invalid = client.get("/validar", params={"t": token[:-3] + "xyz"})
    assert invalid.status_code == 404
    assert "inválido" in invalid.text


def test_qr_url_uses_public_base_url(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://exemplo.test")
    from app.api import routes

    class Req:
        base_url = "http://localhost:8000/"

    assert routes._public_base_url(Req()) == "https://exemplo.test"
    monkeypatch.delenv("PUBLIC_BASE_URL")
    assert routes._public_base_url(Req()) == "http://localhost:8000"
