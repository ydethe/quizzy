from typing import List

from pyicloud import PyiCloudService

from .models import ICloudContact, Config


def read_icloud_contacts(config: Config) -> List[ICloudContact]:
    api = PyiCloudService(config.icloud_account)

    contacts: List[ICloudContact] = []
    for c in api.contacts.all:
        contact = ICloudContact.model_validate(c)
        contacts.append(contact)

    return contacts
