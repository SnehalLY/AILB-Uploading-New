import logging
import os
import ssl
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS

from config import settings
from crypto_utils import decrypt_data, get_public_key
from login import main_to_execute


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIST / "assets"),
    static_url_path="/assets",
)
CORS(
    app,
    resources={
        r"/*": {
            "origins": list(settings.allowed_origins),
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Cache-Control", "Pragma"],
            "expose_headers": ["Content-Type"],
        }
    },
)


@app.get("/api/public-key")
def serve_public_key():
    try:
        public_key_pem = get_public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_key_pem, 200, {"Content-Type": "application/x-pem-file"}
    except Exception:
        logger.exception("Failed to serve the public key")
        return jsonify({"error": "Public key is unavailable"}), 500


@app.post("/api/login")
def handle_login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON request body is required"}), 400

    required = ["username", "password", "question", "answer_sets", "difficulty", "author", "topic", "question_bank"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not settings.imocha_write_enabled:
        logger.warning("iMocha write operations are disabled.")
        return jsonify({"error": "iMocha write operations are disabled by IMOCHA_WRITE_ENABLED=false"}), 503

    try:
        overall_marks = int(data.get("overall_marks", 10))
        num_blanks = int(data.get("num_blanks", 5))
        difficulty = int(data["difficulty"])
    except (TypeError, ValueError):
        return jsonify({"error": "difficulty, overall_marks, and num_blanks must be integers"}), 400
    if overall_marks <= 0 or not 1 <= num_blanks <= 10 or overall_marks < num_blanks:
        return jsonify({"error": "Invalid marks or blank count"}), 400
    if not str(data["answer_sets"]).strip():
        return jsonify({"error": "answer_sets must not be empty"}), 400

    try:
        username = decrypt_data(data["username"])
        password = decrypt_data(data["password"])
        success, failure_reason = main_to_execute(
            username=username,
            password=password,
            question=data["question"],
            answer_sets=data["answer_sets"],
            difficulty=difficulty,
            author=data["author"],
            topic=data["topic"],
            question_bank=data["question_bank"],
            overall_marks=overall_marks,
            num_blanks=num_blanks,
        )
        if success:
            return jsonify({"message": "Successfully uploaded question"}), 200
        return jsonify({"error": f"Upload failed: {failure_reason}"}), 500
    except ValueError:
        return jsonify({"error": "Credential decryption failed"}), 400
    except Exception:
        logger.exception("Question upload failed")
        return jsonify({"error": "Question upload failed"}), 500


@app.get("/openssl-version")
def openssl_version():
    return ssl.OPENSSL_VERSION


@app.get("/")
def serve_frontend():
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/<path:path>")
def serve_frontend_route(path: str):
    if (
        path == "api"
        or path.startswith("api/")
        or path == "assets"
        or path.startswith("assets/")
        or path == "openssl-version"
        or path.startswith("openssl-version/")
    ):
        abort(404)

    requested_file = FRONTEND_DIST / path
    if requested_file.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=False)
