from datetime import datetime
from pathlib import Path
import jwt
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, BaseModel
import requests


def download_geoip_db(db_url: AnyHttpUrl, dest_file: Path):
    import zlib

    res = requests.get(str(db_url))
    data = zlib.decompress(res.content, zlib.MAX_WBITS | 32)

    with open(dest_file, "wb") as f:
        f.write(data)


class QuizzyConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    AES_SECRET: str
    JWT_SECRET: str
    COOKIE_SECRET: str
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: AnyHttpUrl
    OPENID_CONFIG_URL: AnyHttpUrl
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    SERVICE_PASSWORD_POSTGRESQL: str
    SERVICE_USER_POSTGRESQL: str
    POSTGRES_HOST: str
    GEOIP2_DB_URL: AnyHttpUrl

    def load_geoip(self):
        download_geoip_db(self.GEOIP2_DB_URL, self.geoip_pth)

    @property
    def geoip_pth(self) -> Path:
        return Path(".") / "GeoLite2-City.mmdb"


class Examen(BaseModel):
    quizz: str
    email: str
    nom: str
    prenom: str

    def get_encrypted(self) -> str:
        from .config import config
        from .crypto import encrypt_payload

        dt_now = datetime.now().isoformat()
        aes_payload = dict(
            token_creation_date=dt_now, exam_data=encrypt_payload(self.model_dump_json())
        )

        encoded = jwt.encode(aes_payload, config.JWT_SECRET, algorithm="HS256")
        return encoded

    @classmethod
    def from_encrypted(cls, cipher: str):
        from .config import config
        from .crypto import decrypt_payload

        aes_payload = jwt.decode(cipher, config.JWT_SECRET, algorithms="HS256")
        # sdt=aes_payload['token_creation_date']
        # token_creation_date=datetime.fromisoformat(sdt)

        dat = json.loads(decrypt_payload(aes_payload["exam_data"]))

        return cls.model_validate(dat)


config = QuizzyConfig()
config.load_geoip()
