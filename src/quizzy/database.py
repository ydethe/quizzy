from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, create_engine
import geoip2.database
import geoip2.errors
from geoip2.models import City

from .config import config


def get_geoip_info(ip_addr: str) -> City | None:
    # This creates a Reader object. You should use the same object
    # across multiple requests as creation of it is expensive.
    with geoip2.database.Reader(config.geoip_pth) as reader:
        try:
            response = reader.city(ip_addr)
        except geoip2.errors.AddressNotFoundError:
            response = None

    return response


class Etudiant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nom: str
    prenom: str
    passages: list["Passage"] = Relationship(back_populates="etudiant")
    email: str


class Geoip(SQLModel, table=True):
    ip_origine: str | None = Field(default=None, index=True, primary_key=True)
    latitude: float | None = None
    longitude: float | None = None
    accuracy_radius: float | None = None
    city: str | None = None
    country: str | None = None
    passages: list["Passage"] = Relationship(back_populates="geoip")


class Passage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    quiz_nom: str
    quiz_hash: str
    etudiant_id: int = Field(foreign_key="etudiant.id")
    etudiant: Etudiant = Relationship(back_populates="passages")
    ip_origine: str = Field(foreign_key="geoip.ip_origine")
    geoip: Geoip = Relationship(back_populates="passages")
    date: datetime
    reponses: str
    score: float


engine = create_engine(
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:5432/{config.POSTGRES_DB}"
)

SQLModel.metadata.create_all(engine)
