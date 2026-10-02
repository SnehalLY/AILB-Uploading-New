"""Central, fail-fast configuration for the independent project."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

VALID_APP_ENVS = {"development", "staging", "production"}
LEGACY_DATABASE_VALUES = {"counter_db", "counter_collection", "december_2025"}

# SHA-256 fingerprints keep known legacy endpoints out of this repository while
# still allowing startup validation to reject them if they are configured.
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


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip().rstrip("/") for value in os.getenv(name, default).split(",") if value.strip())


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true or false, not {raw!r}")


def _url_fingerprint(url: str) -> str:
    return hashlib.sha256(url.strip().rstrip("/").lower().encode("utf-8")).hexdigest()


def _project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _validate_http_url(name: str, value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{name} must be an absolute http(s) URL: {value!r}")
    if _url_fingerprint(value) in BLOCKED_URL_SHA256:
        raise RuntimeError(f"{name} points to a blocked legacy production service: {value!r}")


@dataclass(frozen=True)
class Settings:
    app_env: str
    frontend_url: str
    allowed_origins: tuple[str, ...]
    imocha_base_url: str
    imocha_write_enabled: bool
    mongo_url: str | None
    mongo_database: str
    mongo_collection: str
    counter_id: str
    rsa_private_key_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")
        settings = cls(
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            frontend_url=frontend_url,
            allowed_origins=_csv("ALLOWED_ORIGINS", frontend_url),
            imocha_base_url=os.getenv("IMOCHA_BASE_URL", "https://app.imocha.io").strip().rstrip("/"),
            imocha_write_enabled=_bool("IMOCHA_WRITE_ENABLED", False),
            mongo_url=os.getenv("MONGO_URL") or None,
            mongo_database=os.getenv("MONGO_DATABASE", "ailbuploading_new").strip(),
            mongo_collection=os.getenv("MONGO_COLLECTION", "counters").strip(),
            counter_id=os.getenv("COUNTER_ID", "local_development").strip(),
            rsa_private_key_path=_project_path(
                os.getenv("RSA_PRIVATE_KEY_PATH", "Backend/private_key.pem")
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.app_env not in VALID_APP_ENVS:
            raise RuntimeError(f"APP_ENV must be one of {sorted(VALID_APP_ENVS)}")
        _validate_http_url("FRONTEND_URL", self.frontend_url)
        if not self.allowed_origins:
            raise RuntimeError("ALLOWED_ORIGINS must contain at least one explicit origin")
        for origin in self.allowed_origins:
            _validate_http_url("ALLOWED_ORIGINS", origin)
        _validate_http_url("IMOCHA_BASE_URL", self.imocha_base_url)
        for name, value in {
            "MONGO_DATABASE": self.mongo_database,
            "MONGO_COLLECTION": self.mongo_collection,
            "COUNTER_ID": self.counter_id,
        }.items():
            if not value:
                raise RuntimeError(f"{name} must not be empty")
            if value.lower() in LEGACY_DATABASE_VALUES:
                raise RuntimeError(f"{name} uses a blocked legacy production value: {value!r}")
        if self.app_env == "production" and not self.mongo_url:
            raise RuntimeError("MONGO_URL is required when APP_ENV=production")
        if self.imocha_write_enabled and self.app_env == "development":
            raise RuntimeError("IMOCHA_WRITE_ENABLED=true is forbidden when APP_ENV=development")


settings = Settings.from_env()
