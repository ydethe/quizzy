import unittest
import json

import yaml
from yaml import BaseLoader

from directus_sync.directus_sync import DirectusDatabase
from directus_sync.models import Config


class TestDirectusSync(unittest.TestCase):
    def test_sync_all(self):
        with open("tests/prod.yml", "r") as f:
            dat = yaml.load(f, Loader=BaseLoader)
        config = Config.model_validate_json(json.dumps(dat))

        db = DirectusDatabase()
        db.load_from_directus(config)

        vcards = db.convert_contacts()
        print(vcards[0].to_vcard())

    def test_icloud(self):
        with open("tests/prod.yml", "r") as f:
            dat = yaml.load(f, Loader=BaseLoader)
        config = Config.model_validate_json(json.dumps(dat))

        db = DirectusDatabase()
        db.load_from_directus(config)
        db.load_from_icloud(config)
        db.upsert_directus(config)
        # for contact in db.contacts.values():
        #     print(contact)


if __name__ == "__main__":
    a = TestDirectusSync()

    # a.test_sync_all()

    a.test_icloud()
