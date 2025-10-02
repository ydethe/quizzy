import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class QuizzyConfig(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    SECRET: str


class Examen(BaseModel):
    quizz: str
    email: str
    nom: str
    prenom: str

    def get_encrypted(self) -> str:
        from .config import config

        encoded = jwt.encode(self.model_dump(), config.SECRET, algorithm="HS256")
        return encoded

    @classmethod
    def from_encrypted(cls, cipher: str):
        from .config import config

        json = jwt.decode(cipher, config.SECRET, algorithms="HS256")
        return cls.model_validate(json)


config = QuizzyConfig()
