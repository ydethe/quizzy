from __future__ import annotations

from typing import List, Optional, Union
from uuid import UUID
from datetime import date, datetime
from enum import Enum
import re

from pydantic import BaseModel, AnyUrl, EmailStr, field_validator, model_validator

# -----------------------------
# Helpers & Enums
# -----------------------------

LANGTAG_RE = re.compile(r"^(?i:[a-z]{2,3})(?:-[A-Za-z0-9]{2,8})*$")  # BCP 47 (loose)
TEL_URI_RE = re.compile(r"^(?i:tel:)?\+?[0-9().\-;ext=,pwt\s]+$")
GEO_URI_RE = re.compile(
    r"^(?i:geo:)-?[0-9]+(?:\.[0-9]+)?,-?[0-9]+(?:\.[0-9]+)?(?:;u=[0-9]+(?:\.[0-9]+)?)?$"
)
TZ_RE = re.compile(r"^(?:Z|[+-](?:0\d|1\d|2[0-3]):?[0-5]\d|[A-Za-z_][A-Za-z0-9_\-/]+)$")


class Gender(str, Enum):
    M = "M"
    F = "F"
    O = "O"  # noqa: E741
    N = "N"
    U = "U"


# -----------------------------
# Component Types
# -----------------------------


class Name(BaseModel):
    family: Optional[str] = None
    given: Optional[str] = None
    additional: List[str] = []
    prefixes: List[str] = []
    suffixes: List[str] = []

    model_config = {"extra": "forbid", "validate_assignment": True, "use_enum_values": True}


class Address(BaseModel):
    po_box: Optional[str] = None
    extended: Optional[str] = None
    street: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    label: Optional[str] = None

    model_config = {"extra": "forbid", "validate_assignment": True}


class Telephone(BaseModel):
    value: str
    type: Optional[List[str]] = None
    pref: Optional[int] = None

    @field_validator("value")
    @classmethod
    def validate_tel(cls, v: str) -> str:
        if not TEL_URI_RE.match(v):
            raise ValueError("tel must be a RFC3966 tel URI or E.164-like number")
        if not v.lower().startswith("tel:"):
            v = "tel:" + v
        v = v.replace(" ", "")
        return v

    @field_validator("pref")
    @classmethod
    def validate_pref(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (1 <= v <= 100):
            raise ValueError("pref must be between 1 and 100")
        return v

    model_config = {"extra": "forbid", "validate_assignment": True}


class Email(BaseModel):
    value: EmailStr
    type: Optional[List[str]] = None
    pref: Optional[int] = None

    @field_validator("pref")
    @classmethod
    def validate_pref(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (1 <= v <= 100):
            raise ValueError("pref must be between 1 and 100")
        return v

    model_config = {"extra": "forbid", "validate_assignment": True}


class Organization(BaseModel):
    units: List[str]

    model_config = {"extra": "forbid", "validate_assignment": True}


class Related(BaseModel):
    uri: Optional[AnyUrl] = None
    email: Optional[EmailStr] = None
    text: Optional[str] = None
    type: Optional[List[str]] = None

    @model_validator(mode="after")
    def check_one_value(self):
        if sum(1 for x in (self.uri, self.email, self.text) if x is not None) != 1:
            raise ValueError("related: exactly one of uri, email, or text must be set")
        return self

    model_config = {"extra": "forbid", "validate_assignment": True}


# -----------------------------
# Root vCard Model
# -----------------------------


class VCard(BaseModel):
    version: str = "4.0"
    fn: str

    n: Optional[Name] = None
    nickname: Optional[List[str]] = None
    photo: Optional[str] = None
    bday: Optional[Union[date, datetime, str]] = None
    anniversary: Optional[Union[date, datetime, str]] = None
    gender: Optional[Gender] = None

    adr: Optional[List[Address]] = None
    tel: Optional[List[Telephone]] = None
    email: Optional[List[Email]] = None

    impp: Optional[List[AnyUrl]] = None
    lang: Optional[List[str]] = None
    tz: Optional[str] = None
    geo: Optional[str] = None

    title: Optional[str] = None
    role: Optional[str] = None
    org: Optional[Organization] = None

    member: Optional[List[Union[AnyUrl, EmailStr]]] = None
    related: Optional[List[Related]] = None

    categories: Optional[List[str]] = None
    note: Optional[str] = None
    prodid: Optional[str] = None
    rev: Optional[datetime] = None
    sound: Optional[AnyUrl] = None

    uid: Optional[Union[AnyUrl, UUID]] = None
    url: Optional[List[AnyUrl]] = None
    key: Optional[List[Union[AnyUrl, str]]] = None

    fburl: Optional[AnyUrl] = None
    caladruri: Optional[AnyUrl] = None
    caluri: Optional[AnyUrl] = None

    @field_validator("version")
    @classmethod
    def version_must_be_40(cls, v: str) -> str:
        if v != "4.0":
            raise ValueError("VERSION must be '4.0' per RFC 6350")
        return v

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for tag in v:
            if not LANGTAG_RE.match(tag):
                raise ValueError(f"Invalid BCP47 language tag: {tag}")
        return v

    @field_validator("tz")
    @classmethod
    def validate_tz(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not TZ_RE.match(v):
            raise ValueError("tz must be an IANA TZID or UTC offset like +02:00 or Z")
        return v

    @field_validator("geo")
    @classmethod
    def validate_geo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not GEO_URI_RE.match(v):
            raise ValueError("geo must be a valid RFC5870 geo: URI")
        return v

    @model_validator(mode="after")
    def check_required(self):
        if not (self.fn and self.fn.strip()):
            raise ValueError("FN (Formatted Name) is required and must be non-empty")
        return self

    model_config = {"extra": "forbid", "validate_assignment": True, "use_enum_values": True}

    # -----------------------------
    # Serialization (to vCard string)
    # -----------------------------
    def to_vcard(self) -> str:
        lines = ["BEGIN:VCARD", f"VERSION:{self.version}", f"FN:{self.fn}"]
        if self.n:
            parts = [
                self.n.family or "",
                self.n.given or "",
                ",".join(self.n.additional) if self.n.additional else "",
                ",".join(self.n.prefixes) if self.n.prefixes else "",
                ",".join(self.n.suffixes) if self.n.suffixes else "",
            ]
            lines.append("N:" + ";".join(parts))
        if self.nickname:
            lines.append("NICKNAME:" + ",".join(self.nickname))
        if self.photo:
            lines.append(f"PHOTO:{self.photo}")
        if self.bday:
            lines.append(f"BDAY:{self.bday}")
        if self.anniversary:
            lines.append(f"ANNIVERSARY:{self.anniversary}")
        if self.gender:
            lines.append(f"GENDER:{self.gender}")
        if self.adr:
            for a in self.adr:
                parts = [
                    a.po_box or "",
                    a.extended or "",
                    a.street or "",
                    a.locality or "",
                    a.region or "",
                    a.postal_code or "",
                    a.country or "",
                ]
                lines.append("ADR:" + ";".join(parts))
                if a.label:
                    lines.append(f"LABEL:{a.label}")
        if self.tel:
            for t in self.tel:
                lines.append(f"TEL:{t.value}")
        if self.email:
            for e in self.email:
                lines.append(f"EMAIL:{e.value}")
        if self.impp:
            for i in self.impp:
                lines.append(f"IMPP:{i}")
        if self.lang:
            for lng in self.lang:
                lines.append(f"LANG:{lng}")
        if self.tz:
            lines.append(f"TZ:{self.tz}")
        if self.geo:
            lines.append(f"GEO:{self.geo}")
        if self.title:
            lines.append(f"TITLE:{self.title}")
        if self.role:
            lines.append(f"ROLE:{self.role}")
        if self.org:
            lines.append("ORG:" + ";".join(self.org.units))
        if self.member:
            for m in self.member:
                lines.append(f"MEMBER:{m}")
        if self.related:
            for r in self.related:
                if r.uri:
                    lines.append(f"RELATED:{r.uri}")
                elif r.email:
                    lines.append(f"RELATED:mailto:{r.email}")
                else:
                    lines.append(f"RELATED:{r.text}")
        if self.categories:
            lines.append("CATEGORIES:" + ",".join(self.categories))
        if self.note:
            lines.append(f"NOTE:{self.note}")
        if self.prodid:
            lines.append(f"PRODID:{self.prodid}")
        if self.rev:
            lines.append(f"REV:{self.rev.isoformat()}")
        if self.sound:
            lines.append(f"SOUND:{self.sound}")
        if self.uid:
            lines.append(f"UID:{self.uid}")
        if self.url:
            for u in self.url:
                lines.append(f"URL:{u}")
        if self.key:
            for k in self.key:
                lines.append(f"KEY:{k}")
        if self.fburl:
            lines.append(f"FBURL:{self.fburl}")
        if self.caladruri:
            lines.append(f"CALADRURI:{self.caladruri}")
        if self.caluri:
            lines.append(f"CALURI:{self.caluri}")
        lines.append("END:VCARD")
        return "\r\n".join(lines)
