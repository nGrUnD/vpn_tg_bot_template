from __future__ import annotations

import base64
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


def verify_wata_webhook_body(*, raw_body: bytes, signature_b64: str, public_key_pem: str) -> bool:
    """
    RSA PKCS#1 v1.5 + SHA512, как в доке WATA (openssl_verify SHA512).
    """
    try:
        sig = base64.b64decode(signature_b64, validate=True)
    except Exception:
        logger.info("WATA webhook: невалидная base64 подписи")
        return False
    try:
        pub = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        pub.verify(sig, raw_body, padding.PKCS1v15(), hashes.SHA512())
        return True
    except Exception:
        logger.info("WATA webhook: подпись не сошлась")
        return False
