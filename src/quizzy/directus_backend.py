from datetime import date, datetime
from typing import Any, Callable, Dict, Iterable, Iterator, List, TypeVar
from pydantic import BaseModel
import requests

from tqdm import tqdm

from . import logger
from .models import (
    Config,
    Contact,
    Adresse,
    ContactsAdresse,
    Email,
    Experience,
    Organisation,
    OrganisationsAdresse,
    Telephone,
)


T = TypeVar("T", bound=BaseModel)


def request_asset(config: Config, asset_id: str | None) -> bytes:
    if asset_id is None:
        return b""

    # https://directus.io/docs/getting-started/use-the-api
    res = requests.get(
        f"{config.directus_url}/assets/{asset_id}",
        headers={"Authorization": f"Bearer {config.directus_token}"},
    )

    if res.status_code == 200:
        return res.content
    else:
        return b""


def upsert_collection(config: Config, collection: str, items: Iterable[Dict[Any, Any]]):
    for item in tqdm(items):
        res = requests.post(
            f"{config.directus_url}/items/{collection}",
            params={"upsert": "id"},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.directus_token}",
            },
            json=item,
        )
        if res.status_code != 200:
            logger.error(res.content)

    pass


def request_collection(config: Config, collection: str) -> List[Dict[Any, Any]]:
    # https://directus.io/docs/getting-started/use-the-api
    res = requests.get(
        f"{config.directus_url}/items/{collection}",
        headers={"Authorization": f"Bearer {config.directus_token}"},
    )
    data = res.json()

    return data["data"]


def read_item(
    config: Config, collection: str, model_factory: Callable[[Dict[Any, Any]], T]
) -> Iterator[T]:
    data = request_collection(config, collection=collection)
    for dat in data:
        item = model_factory(dat)
        item.model_dump()
        yield item


def read_contacts(config: Config) -> Iterator[Contact]:
    for contact in read_item(config, collection="Contacts", model_factory=Contact.model_validate):
        contact.Photo_Content = request_asset(config, contact.Photo)

        yield contact


def read_adresses(config: Config) -> Iterator[Adresse]:
    for adresse in read_item(config, collection="Adresse", model_factory=Adresse.model_validate):
        yield adresse


def read_contact_adresses(config: Config) -> Iterator[ContactsAdresse]:
    for con_adr in read_item(
        config, collection="Contacts_Adresse", model_factory=ContactsAdresse.model_validate
    ):
        yield con_adr


def read_experience(config: Config) -> Iterator[Experience]:
    for expe in read_item(config, collection="Experience", model_factory=Experience.model_validate):
        yield expe


def read_organisation(config: Config) -> Iterator[Organisation]:
    for expe in read_item(
        config, collection="Organisation", model_factory=Organisation.model_validate
    ):
        yield expe


def read_organisation_adresses(config: Config) -> Iterator[OrganisationsAdresse]:
    for orga_adr in read_item(
        config, collection="Organisation_Adresse", model_factory=OrganisationsAdresse.model_validate
    ):
        yield orga_adr


def read_telephone(config: Config) -> Iterator[Telephone]:
    for telephone in read_item(
        config, collection="Telephone", model_factory=Telephone.model_validate
    ):
        yield telephone


def read_email(config: Config) -> Iterator[Email]:
    for email in read_item(config, collection="Email", model_factory=Email.model_validate):
        yield email


def upsert_contact(config: Config, contacts: Iterable[Contact]):
    items: List[Dict[str, Any]] = []
    for con in contacts:
        item = con.model_dump()
        item.pop("Photo_Content", None)
        item.pop("Photo", None)
        item.pop("Adresses", None)
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)
            elif isinstance(item[k], datetime):
                dtt: datetime = item[k]
                item[k] = dtt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            elif isinstance(item[k], date):
                dt: date = item[k]
                item[k] = dt.strftime("%Y-%m-%dT00:00:00.000Z")
        # '2025-09-01T12:05:03.252Z'
        # json.dumps(item)
        items.append(item)

    upsert_collection(config, "Contacts", items)


def upsert_adresse(config: Config, adresses: Iterable[Adresse]):
    items: List[Dict[str, Any]] = []
    for adr in adresses:
        adr.compute_coordinates()

        item = adr.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)
            elif isinstance(item[k], datetime):
                dtt: datetime = item[k]
                item[k] = dtt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            elif isinstance(item[k], date):
                dt: date = item[k]
                item[k] = dt.strftime("%Y-%m-%dT00:00:00.000Z")
        # '2025-09-01T12:05:03.252Z'
        # json.dumps(item)
        items.append(item)

    upsert_collection(config, "Adresse", items)


def upsert_email(config: Config, emails: Iterable[Email]):
    items: List[Dict[str, Any]] = []
    for mail in emails:
        item = mail.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)

        items.append(item)

    upsert_collection(config, "Email", items)


def upsert_experience(config: Config, experiences: Iterable[Experience]):
    items: List[Dict[str, Any]] = []
    for expe in experiences:
        item = expe.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)

        items.append(item)

    upsert_collection(config, "Experience", items)


def upsert_organisation(config: Config, organisations: Iterable[Organisation]):
    items: List[Dict[str, Any]] = []
    for orga in organisations:
        item = orga.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)

        items.append(item)

    upsert_collection(config, "Organisation", items)


def upsert_telephone(config: Config, telephones: Iterable[Telephone]):
    items: List[Dict[str, Any]] = []
    for tel in telephones:
        item = tel.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)

        items.append(item)

    upsert_collection(config, "Telephone", items)


def upsert_contact_adresse(config: Config, contact_adresse: Iterable[ContactsAdresse]):
    items: List[Dict[str, Any]] = []
    for con_adr in contact_adresse:
        item = con_adr.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)

        items.append(item)

    upsert_collection(config, "Contacts_Adresse", items)


def upsert_orga_adresse(config: Config, orga_adresse: Iterable[OrganisationsAdresse]):
    items: List[Dict[str, Any]] = []
    for org_adr in orga_adresse:
        item = org_adr.model_dump()
        for k in list(item.keys()):
            if item[k] is None or item[k] == "":
                item.pop(k)

        items.append(item)

    upsert_collection(config, "Organisation_Adresse", items)
