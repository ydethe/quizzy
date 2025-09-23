import base64
from datetime import date, datetime
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from pydantic import HttpUrl, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from geopy.location import Location
import diskcache as dc
import gender_guesser.detector as gender  # type: ignore

from . import logger, geolocator
from .vcard import Gender, Name, VCard
from .vcard import Address as VAddress
from .vcard import Telephone as VTelephone
from .vcard import Email as VEmail


cache = dc.Cache("./.mycache")


class CiviliteEnum(str, Enum):
    MR = "Mr"
    MME = "Mme"
    MLLE = "Mlle"
    FRERE = "Frère"
    SOEUR = "Soeur"
    PERE = "Père"


class ParticuleEnum(str, Enum):
    NONE = " "
    DE = " de "
    DU = " du "
    DEL = " de l'"
    DELA = " de la "
    LE = " le "


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
    )

    directus_url: HttpUrl
    directus_token: str
    icloud_account: str


class BaseDirectusModel(BaseModel):
    id: Optional[int | None] = None
    user_created: Optional[str | None] = None
    date_created: Optional[datetime | None] = None
    user_updated: Optional[str | None] = None
    date_updated: Optional[datetime | None] = None


class Coordinate(BaseModel):
    type: str
    coordinates: List[float]


@cache.memoize()
def geocode(address: str) -> Coordinate | None:
    coord = None

    location: Location | None = geolocator.geocode(address)  # type: ignore
    if location is not None:
        coord = Coordinate(type="Point", coordinates=[location.longitude, location.latitude])
    else:
        logger.warning(f"Failed geocoding {address}")

    time.sleep(1)

    return coord


class Adresse(BaseDirectusModel):
    Adresse: str
    Code_postal: str
    Ville: str
    Pays: str
    Coordonnees: Optional[Coordinate | None] = None

    def __str__(self) -> str:
        return f"{self.Adresse}, {self.Code_postal}, {self.Ville}, {self.Pays}"

    def compute_coordinates(self):
        self.Coordonnees = geocode(str(self))

    def to_vcard(self) -> VAddress:
        adr = VAddress(
            street=self.Adresse,
            locality=self.Ville,
            postal_code=self.Code_postal,
            country=self.Pays,
        )
        return adr


class ContactsAdresse(BaseModel):
    id: Optional[int | None] = None
    Contacts_id: int
    Adresse_id: int
    Type: str

    def __str__(self) -> str:
        return f"{self.Contacts_id},{self.Adresse_id}"


class Experience(BaseDirectusModel):
    Contact: int
    Type: str
    Organisation: int
    Date_debut: Optional[date | None] = None
    Date_fin: Optional[date | None] = None
    Intitule: str
    Description: Optional[str | None] = None

    def __str__(self) -> str:
        return f"{self.Contact},{self.Organisation},{self.Intitule},{self.Date_debut}"


class Organisation(BaseDirectusModel):
    Nom: str
    Site_web: Optional[str | None] = None
    Type: str
    Adresse: List[int] = []

    def __str__(self) -> str:
        return f"{self.Nom}"


class OrganisationsAdresse(BaseModel):
    id: Optional[int | None] = None
    Organisation_id: int
    Adresse_id: int

    def __str__(self) -> str:
        return f"{self.Organisation_id},{self.Adresse_id}"


class Telephone(BaseDirectusModel):
    Telephone: str
    Contact: int
    Prefere: bool
    Type: str

    def __str__(self) -> str:
        return f"{self.Telephone}"

    def to_vcard(self) -> VTelephone:
        vtel = VTelephone(value=self.Telephone, type=[self.Type], pref=2 - int(self.Prefere))
        return vtel


class Email(BaseDirectusModel):
    Email: str
    Contact: int
    Prefere: bool
    Type: str

    def __str__(self) -> str:
        return f"{self.Email}"

    def to_vcard(self) -> VEmail:
        vmail = VEmail(value=self.Email, type=[self.Type], pref=2 - int(self.Prefere))
        return vmail


class Contact(BaseDirectusModel):
    Nom: str
    Prenom: str
    Particule: str
    Civilite: CiviliteEnum
    Nom_de_naissance: Optional[str] = ""
    Date_de_naissance: Optional[date | None] = None
    Site_web: Optional[str] = ""
    Profile_LinkedIn: Optional[str] = ""
    Notes: Optional[str] = ""
    Photo: Optional[str] = ""
    Photo_Content: Optional[bytes] = b""
    Directus_User: Optional[str] = ""
    Adresses: List[int] = []

    def __str__(self) -> str:
        return f"{self.Civilite.value} {self.Prenom}{self.Particule}{self.Nom}"

    def to_vcard(
        self,
        adresses: Dict[int, Adresse],
        contact_adresses: Dict[int, ContactsAdresse],
        experiences: Dict[int, Experience],
        organisations: Dict[int, Organisation],
        organisation_adresses: Dict[int, OrganisationsAdresse],
        telephones: Dict[int, Telephone],
        emails: Dict[int, Email],
    ) -> VCard:
        list_adr: List[VAddress] = []
        for ca in contact_adresses.values():
            if ca.Contacts_id == self.id:
                vadr = adresses[ca.Adresse_id].to_vcard()
                vadr.label = ca.Type
                list_adr.append(vadr)

        list_tel: List[VTelephone] = []
        for tel in telephones.values():
            if tel.Contact == self.id:
                vtel = tel.to_vcard()
                list_tel.append(vtel)

        list_mail: List[VEmail] = []
        for mail in emails.values():
            if mail.Contact == self.id:
                vmail = mail.to_vcard()
                list_mail.append(vmail)

        last_expe: Experience | None = None
        last_expe_date = self.Date_de_naissance
        for exp in experiences.values():
            if exp.Date_debut > last_expe_date:
                last_expe_date = exp.Date_debut
                last_expe = exp

        role = None
        if last_expe is not None:
            orga = organisations[last_expe.Organisation]

            role = f"{last_expe.Intitule} @ {orga.Nom}"

            for org_adr in organisation_adresses.values():
                if org_adr.Organisation_id == orga.id:
                    exp_adr = adresses[org_adr.Adresse_id]

                    vadr = exp_adr.to_vcard()
                    vadr.label = "Pro"
                    list_adr.append(vadr)

                    break

        vcard = VCard(
            prodid=f"{self.id}",
            fn=f"{self.Prenom}{self.Particule}{self.Nom}",
            n=Name(
                family=f"{self.Particule}{self.Nom}".strip(),
                given=self.Prenom,
                prefixes=[self.Civilite.value],
            ),
            anniversary=self.Date_de_naissance,
            gender=Gender.M if self.Civilite.value in ["Mr", "Frère", "Père"] else Gender.F,
            adr=list_adr,
            tel=list_tel,
            email=list_mail,
            title=self.Civilite.value,
            role=role,
        )
        if self.Photo_Content is not None and len(self.Photo_Content) > 0:
            b64_photo = base64.b64encode(self.Photo_Content).decode("ascii")

            vcard.photo = f"data:image/jpeg;base64,{b64_photo}"

        return vcard


class ICloudFieldLabel(BaseModel):
    field: str
    label: Optional[str] = "HOME"


class ICloudUrl(ICloudFieldLabel):
    pass


class ICloudProfile(BaseModel):
    pass


class ICloudphones(ICloudFieldLabel):
    pass


class ICloudEmail(ICloudFieldLabel):
    pass


class ICloudAddresseField(BaseModel):
    country: Optional[str] = "France"
    city: Optional[str] = ""
    countryCode: Optional[str] = "fr"
    street: Optional[str] = ""
    postalCode: Optional[str] = ""


class ICloudAddresse(BaseModel):
    field: ICloudAddresseField
    label: Optional[str] = "HOME"


class ICloudRelatedName(ICloudFieldLabel):
    pass


class ICloudDate(BaseModel):
    field: date
    label: Optional[str] = "HOME"


class ICloudPhoto(BaseModel):
    url: str


class ICloudContact(BaseModel):
    nickName: Optional[str] = ""
    isCompany: Optional[bool] = False
    isGuardianApproved: Optional[bool] = True
    streetAddresses: List[ICloudAddresse] = []
    urls: List[ICloudUrl] = []
    normalized: Optional[str] = ""
    jobTitle: Optional[str] = ""
    phones: List[ICloudphones] = []
    etag: Optional[str] = ""
    emailAddresses: List[ICloudEmail] = []
    middleName: Optional[str] = ""
    contactId: Optional[str] = ""
    companyName: Optional[str] = ""
    relatedNames: List[ICloudRelatedName] = []
    lastName: Optional[str] = ""
    firstName: Optional[str] = ""
    photo: Optional[ICloudPhoto | None] = None
    notes: Optional[str] = ""
    birthday: Optional[date | None] = None
    dates: List[ICloudDate] = []
    whitelisted: Optional[bool] = True

    def analyse_name(
        self, detector: gender.Detector
    ) -> Tuple[CiviliteEnum, str, ParticuleEnum, str]:
        Prenom = self.firstName if self.firstName is not None else ""
        g = detector.get_gender(Prenom)  # type: ignore
        if g == "male" or g == "andy":
            Civilite = CiviliteEnum.MR
        else:
            Civilite = CiviliteEnum.MME

        Nom: str = self.lastName.strip().title() if self.lastName is not None else ""
        NomLow = Nom.lower()
        if NomLow.startswith("de "):
            Particule = ParticuleEnum.DE
            Nom = Nom[3:]
        elif NomLow.endswith(" (de)"):
            Particule = ParticuleEnum.DE
            Nom = Nom[:-5]
        elif NomLow.startswith("du "):
            Particule = ParticuleEnum.DU
            Nom = Nom[3:]
        elif NomLow.endswith(" (du)"):
            Particule = ParticuleEnum.DU
            Nom = Nom[:-5]
        elif NomLow.startswith("le "):
            Particule = ParticuleEnum.LE
            Nom = Nom[3:]
        elif NomLow.endswith(" (le)"):
            Particule = ParticuleEnum.LE
            Nom = Nom[:-5]
        elif NomLow.startswith("de l'"):
            Particule = ParticuleEnum.DEL
            Nom = Nom[5:]
        elif NomLow.endswith(" (de l')"):
            Particule = ParticuleEnum.DEL
            Nom = Nom[:-8]
        elif NomLow.startswith("de la "):
            Particule = ParticuleEnum.DELA
            Nom = Nom[6:]
        elif NomLow.endswith(" (de la)"):
            Particule = ParticuleEnum.DELA
            Nom = Nom[:-8]
        else:
            Particule = ParticuleEnum.NONE

        return Civilite, Prenom, Particule, Nom
