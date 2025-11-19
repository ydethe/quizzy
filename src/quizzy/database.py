from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, create_engine

from .config import config


class Etudiant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nom: str
    prenom: str
    passages: list["Passage"] = Relationship(back_populates="etudiant")
    email: str


class Passage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    quiz_nom: str
    quiz_hash: str
    etudiant_id: int | None = Field(default=None, foreign_key="etudiant.id")
    etudiant: Etudiant | None = Relationship(back_populates="passages")
    date: datetime
    reponses: str
    score: float
    ip_origine: str


engine = create_engine(
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:5432/{config.POSTGRES_DB}"
)

SQLModel.metadata.create_all(engine)
