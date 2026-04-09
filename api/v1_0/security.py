import time
import hmac
import hashlib
from flask import request
from Crypto.Cipher import AES
from base64 import b64decode
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
import config.connection as conn

AES_PASSPHRASE = "7ZXYSAH123456"

def verify_signature():
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")

    if not signature or not timestamp:
        return False, "Missing signature"

    # Validasi timestamp (maksimal selisih 10 detik)
    try:
        ts = int(timestamp)
    except:
        return False, "Invalid timestamp"

    if abs(time.time() - ts) > 10:
        return False, "Timestamp expired"

    # Body untuk signing
    body = request.get_data(as_text=True)

    # Signature expected
    expected = hmac.new(
        AES_PASSPHRASE.encode(),
        f"{timestamp}{body}".encode(),
        hashlib.sha256
    ).hexdigest()

    # Perbandingan aman
    if not hmac.compare_digest(signature, expected):
        return False, "Invalid signature"

    return True, "OK"


def decrypt_aes_base64(ciphertext_b64: str, iv_b64: str, passphrase: str) -> str:
    key = passphrase.ljust(32, "0").encode("utf-8")

    iv = b64decode(iv_b64)
    ct = b64decode(ciphertext_b64)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ct)

    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid padding length")
    data = padded[:-pad_len]
    return data.decode("utf-8")

def single_session_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Verifikasi JWT dulu
        verify_jwt_in_request()

        user_id = get_jwt_identity()
        raw_token = get_jwt()  # ini dict claim JWT

        # Ambil token yang sedang dipakai dari header
        from flask import request
        auth_header = request.headers.get("Authorization", "")
        current_token = auth_header.replace("Bearer ", "").strip()

        # Bandingkan dengan yang ada di DB
        cursor = conn.dsn().cursor()
        cursor.execute(
            "SELECT secret_key FROM dbo.user WHERE userid = ?", user_id
        )
        row = cursor.fetchone()
        cursor.close()

        # ===== DEBUG =====
        print(f"\n{'=' * 60}")
        print(f"[SESSION] user        : {user_id}")
        print(f"[SESSION] header token: {current_token[:50] if current_token else 'KOSONG'}")
        print(f"[SESSION] db token    : {row[0][:50] if row and row[0] else 'NULL'}")
        print(f"[SESSION] cocok       : {row[0] == current_token if row and row[0] else False}")
        print(f"{'=' * 60}\n")
        # ===== END DEBUG =====

        if not row or row[0] != current_token:
            return jsonify({
                "msg": "Sesi kamu telah berakhir karena login di perangkat lain"
            }), 401

        return fn(*args, **kwargs)
    return wrapper


