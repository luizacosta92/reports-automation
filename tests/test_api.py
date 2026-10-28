from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app


client = TestClient(app)


def _xlsx_file(*, nominal: float = 10, readings: tuple[float, ...] = (10.1, 10.3)):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Cliente", "Schulz S.A."])
    sheet.append(["Tecnico Executante", "Maria"])
    sheet.append([])
    sheet.append(["Parametro", "Nominal", "Tol +", "Tol -", "Medida 1", "Medida 2"])
    sheet.append(["P1", nominal, 0.2, -0.2, *readings])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return {
        "file": (
            "calibracao.xlsx",
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_processes_approved_calibration():
    response = client.post(
        "/api/v1/calibrations/process",
        files=_xlsx_file(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"] == {"cliente": "Schulz S.A.", "tecnico": "Maria"}
    assert body["parecer_final"] == "APROVADO"
    assert body["resultados"][0]["status"] == "DENTRO_DA_TOLERANCIA"


def test_processes_rejected_calibration():
    response = client.post(
        "/api/v1/calibrations/process",
        files=_xlsx_file(readings=(10.5, 10.6)),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parecer_final"] == "REPROVADO"
    assert body["resultados"][0]["status"] == "FORA_DA_TOLERANCIA"


def test_rejects_non_xlsx_file():
    response = client.post(
        "/api/v1/calibrations/process",
        files={"file": ("calibracao.csv", b"parametro,nominal", "text/csv")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Envie somente arquivos .xlsx."


def test_rejects_invalid_xlsx_file():
    response = client.post(
        "/api/v1/calibrations/process",
        files={"file": ("calibracao.xlsx", b"arquivo invalido", "application/octet-stream")},
    )

    assert response.status_code == 422
    assert "não foi possível ler" in response.json()["detail"].lower()


def test_requires_file_field():
    response = client.post("/api/v1/calibrations/process")

    assert response.status_code == 422
