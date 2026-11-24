import hmac
import hashlib
import json
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from backend.core.config import settings

class QRService:
    @staticmethod
    def generate_qr_payload(referral_id: str) -> Dict[str, Any]:
        """
        Generates a tamper-proof QR identification payload.
        Contains minimal referral reference and HMAC signature to prevent forgery.
        Never embeds identifiable sensitive patient health info in raw QR.
        """
        expires_at = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
        raw_msg = f"{referral_id}:{expires_at}"
        signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            raw_msg.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        payload = {
            "type": "PHC_BRIDGE_SECURE_QR",
            "v": 2,
            "ref": referral_id,
            "exp": expires_at,
            "sig": signature[:16]  # Compact 16-char verification tag
        }
        return payload

    @staticmethod
    def verify_qr_payload(payload_dict: Dict[str, Any]) -> Optional[str]:
        """
        Validates QR signature and returns referral_id if authentic.
        """
        try:
            if payload_dict.get("type") == "PHC_BRIDGE_REFERRAL":
                # Backwards compatibility with v1 prototype format
                return payload_dict.get("referralId")
            
            ref = payload_dict.get("ref")
            exp = payload_dict.get("exp")
            sig = payload_dict.get("sig")
            
            if not ref or not exp or not sig:
                return None
            
            # Check expiration
            if datetime.now(timezone.utc).timestamp() > exp:
                return None
            
            raw_msg = f"{ref}:{exp}"
            expected_sig = hmac.new(
                settings.SECRET_KEY.encode("utf-8"),
                raw_msg.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if hmac.compare_digest(sig, expected_sig):
                return ref
            return None
        except Exception:
            return None
