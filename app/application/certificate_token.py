"""Identificador e token de validacao do certificado.

O MVP nao possui banco de dados. Por isso, a autenticidade do certificado e
garantida por um token assinado (HMAC-SHA256) que vai dentro do QR Code: se
alguem alterar qualquer dado do token, a assinatura deixa de conferir.
"""

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

DEFAULT_SECRET = "schulz-chave-de-desenvolvimento"
SECRET_ENV = "CERTIFICATE_SECRET"


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _secret() -> bytes:
    return os.environ.get(SECRET_ENV, DEFAULT_SECRET).encode("utf-8")


def _sign(message: str) -> str:
    return _b64encode(hmac.new(_secret(), message.encode("ascii"), hashlib.sha256).digest())


def result_digest(result: dict) -> str:
    """Hash SHA-256 do resultado completo (metadados, pontos e parecer)."""
    canonical = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def issue_certificate(result: dict, issued_at: datetime | None = None) -> dict:
    """Gera o identificador, a data de emissao e o token do certificado."""
    issued_at = (issued_at or datetime.now(timezone.utc)).replace(microsecond=0)
    digest = result_digest(result)
    rows = result.get("resultados", [])
    outside = sum(1 for row in rows if row.get("status") == "FORA_DA_TOLERANCIA")
    metadata = result.get("metadata", {})

    certificate_id = f"CERT-{issued_at:%Y%m%d}-{digest[:8].upper()}"
    payload = {
        "v": 1,
        "id": certificate_id,
        "em": issued_at.isoformat(),
        "p": result.get("parecer_final", ""),
        "n": len(rows),
        "f": outside,
        "c": metadata.get("cliente", ""),
        "t": metadata.get("tecnico", ""),
        "h": digest[:16],
    }
    body = _b64encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return {
        "id": certificate_id,
        "issued_at": issued_at,
        "digest": digest,
        "token": f"{body}.{_sign(body)}",
    }


def verify_token(token: str) -> dict | None:
    """Devolve os dados do certificado se a assinatura conferir; senao, None."""
    try:
        body, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(body)):
            return None
        payload = json.loads(_b64decode(body).decode("utf-8"))
    except (ValueError, UnicodeError):
        return None
    return payload if isinstance(payload, dict) and payload.get("v") == 1 else None
