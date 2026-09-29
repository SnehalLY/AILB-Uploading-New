"""Round-robin backend coordinator for the independent project."""

import hashlib
import os
from threading import Lock
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS


load_dotenv()

# Fingerprints of legacy services are intentionally stored instead of their URLs.
BLOCKED_URL_SHA256 = {
    "0dd5e318c4c92dcd02e4b8160ff0309e9565d324fb3727030bdf9fc5edd3056b",
    "666ee4f9544cc6591c340bc75cc44d5023fc83448206457eeb9dae6f2d7fd80e",
    "dd3305481c77cf85ab058cd172724a8486ab3a4136851883f2ce022687bd4069",
    "6c94d3db6229a1fe93e1174a06b49cda02e87e612e08a7c554df45039f8eb6b4",
    "d2075c3a87c9c337c13561a132d68b99ec9bc54611dd193f1a9791f65edb5c28",
    "f8b52baeb089a58c59c7b1f984d140d2be5be599df550d27c16d5be4ed3917bd",
    "23e42987a13ad4b750974ca4116e6335b3ed523b3531876ed3644e51c124a622",
    "e959eeac4854ff1459ef4926f5ff2c294f886e450def863c4b29273a59119bca",
    "95ecd961eeaef05e42acaf81363761381e0202bc57d68f16387def260d133f60",
    "97ed2289de0402ff0417354e04c8d4a8463fe8a03de0b92832752d71fea3352d",
    "6db932faceed65561111433010fb62c3137602d088f6e696b34cf26dc5fc6216",
    "2fdec184563a4116686814d900f0f6ffc71b47008c061c28b0060b9665c7cf59",
    "f743c7845a512de1f0c6236bde8aad46ec24d85d2a87f1337597fafebb174229",
}


def csv_env(name: str, default: str) -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, default).split(",") if item.strip()]


def validate_url(name: str, value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{name} contains an invalid URL: {value!r}")
    fingerprint = hashlib.sha256(value.lower().rstrip("/").encode("utf-8")).hexdigest()
    if fingerprint in BLOCKED_URL_SHA256:
        raise RuntimeError(f"{name} contains a blocked legacy production URL: {value!r}")


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")
BACKEND_URLS = csv_env("BACKEND_URLS", "http://localhost:5001,http://localhost:5002")
ALLOWED_ORIGINS = csv_env("ALLOWED_ORIGINS", FRONTEND_URL)
validate_url("FRONTEND_URL", FRONTEND_URL)
for configured_url in BACKEND_URLS:
    validate_url("BACKEND_URLS", configured_url)
for configured_url in ALLOWED_ORIGINS:
    validate_url("ALLOWED_ORIGINS", configured_url)

if not BACKEND_URLS:
    raise RuntimeError("BACKEND_URLS must contain at least one backend")
if not ALLOWED_ORIGINS:
    raise RuntimeError("ALLOWED_ORIGINS must contain at least one frontend origin")

app = Flask(__name__)
CORS(app, origins=ALLOWED_ORIGINS)
index = 0
lock = Lock()


@app.get("/next-backend")
def next_backend():
    global index
    with lock:
        url = BACKEND_URLS[index % len(BACKEND_URLS)]
        index = (index + 1) % len(BACKEND_URLS)
    return jsonify({"backend_url": url})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
