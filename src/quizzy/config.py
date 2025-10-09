from datetime import datetime
import jwt
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, BaseModel


class QuizzyConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    AES_SECRET: str
    JWT_SECRET: str
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: AnyHttpUrl
    APP_SLUG: str
    OPENID_CONFIG_URL: AnyHttpUrl


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
