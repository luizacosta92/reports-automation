"""Geracao do certificado em PDF (reportlab) com QR Code de validacao."""

from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLUE = colors.HexColor("#1c5f98")
GREEN = colors.HexColor("#1f8f5a")
RED = colors.HexColor("#c0392b")


class _QrCode(Flowable):
    def __init__(self, url: str, size: float = 34 * mm) -> None:
        super().__init__()
        widget = QrCodeWidget(url, barLevel="M")
        x1, y1, x2, y2 = widget.getBounds()
        self.size = size
        self.drawing = Drawing(size, size, transform=[size / (x2 - x1), 0, 0, size / (y2 - y1), 0, 0])
        self.drawing.add(widget)
        self.width = self.height = size

    def draw(self) -> None:
        renderPDF.draw(self.drawing, self.canv, 0, 0)


def _fmt(value: float) -> str:
    return f"{value:.4f}".replace(".", ",")


def build_certificate_pdf(result: dict, certificate: dict, validation_url: str) -> bytes:
    """Monta o PDF a partir do resultado processado e dos dados de emissao."""
    styles = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=styles["Title"], textColor=BLUE, fontSize=18, spaceAfter=2)
    small = ParagraphStyle("s", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555"))
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=9.5, leading=13)
    cell = ParagraphStyle("c", parent=styles["Normal"], fontSize=8.5, leading=10)

    approved = result["parecer_final"] == "APROVADO"
    metadata = result.get("metadata", {})
    rows = result["resultados"]

    story = [
        Paragraph("CERTIFICADO DE CALIBRAÇÃO", title),
        Paragraph("Reports Automation - Schulz S.A. | Projeto Aplicado III - SENAI/SC", small),
        Spacer(1, 6 * mm),
    ]

    info = Table(
        [
            ["Certificado nº", certificate["id"]],
            ["Emitido em (UTC)", certificate["issued_at"].strftime("%d/%m/%Y %H:%M:%S")],
            ["Cliente / solicitante", metadata.get("cliente", "Não informado")],
            ["Técnico / metrologista", metadata.get("tecnico", "Não informado")],
            ["Pontos de ensaio", str(len(rows))],
        ],
        colWidths=[45 * mm, 125 * mm],
    )
    info.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story += [info, Spacer(1, 6 * mm)]

    header = ["Parâmetro", "Nominal", "Leituras", "Média", "Erro sistemático", "LEA", "Situação"]
    data = [header]
    for row in rows:
        ok = row["status"] == "DENTRO_DA_TOLERANCIA"
        data.append(
            [
                Paragraph(str(row["parametro"]), cell),
                _fmt(row["nominal"]),
                Paragraph("; ".join(_fmt(v) for v in row["leituras"]), cell),
                _fmt(row["media"]),
                _fmt(row["erro_sistematico"]),
                _fmt(row["lea"]),
                "Dentro" if ok else "Fora",
            ]
        )
    table = Table(
        data,
        colWidths=[30 * mm, 20 * mm, 38 * mm, 20 * mm, 29 * mm, 16 * mm, 17 * mm],
        repeatRows=1,
    )
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c8d0d8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
    ]
    for index, row in enumerate(rows, start=1):
        ok = row["status"] == "DENTRO_DA_TOLERANCIA"
        style.append(("TEXTCOLOR", (6, index), (6, index), GREEN if ok else RED))
        style.append(("FONTNAME", (6, index), (6, index), "Helvetica-Bold"))
    table.setStyle(TableStyle(style))
    story += [table, Spacer(1, 5 * mm)]

    story.append(
        Paragraph(
            "Erro sistemático = média das leituras - valor nominal. O ponto está dentro da "
            "tolerância quando |erro sistemático| &lt;= LEA. O parecer é APROVADO somente se "
            "todos os pontos estiverem dentro.",
            normal,
        )
    )
    story.append(Spacer(1, 5 * mm))

    opinion_style = ParagraphStyle(
        "o", parent=styles["Heading2"], textColor=GREEN if approved else RED, spaceAfter=0
    )
    verdict = Table(
        [
            [
                [Paragraph("PARECER FINAL", small), Paragraph(result["parecer_final"], opinion_style)],
                [
                    _QrCode(validation_url),
                ],
                Paragraph(
                    "Para validar este certificado, aponte a câmera do celular para o QR Code. "
                    "A consulta confere a assinatura digital do documento.<br/>"
                    f"<font size=7 color='#777777'>Hash do resultado (SHA-256): {certificate['digest'][:32]}...</font>",
                    small,
                ),
            ]
        ],
        colWidths=[50 * mm, 40 * mm, 80 * mm],
    )
    verdict.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d0d8"))]))
    story.append(verdict)

    buffer = BytesIO()
    SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Certificado {certificate['id']}",
        author="Reports Automation",
    ).build(story)
    return buffer.getvalue()
