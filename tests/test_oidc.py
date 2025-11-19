import unittest

from quizzy.auth import load_discovery_document


class TestOIDC(unittest.TestCase):
    def test_config(self):
        doc = load_discovery_document(
            "https://authentik.johncloud.fr/application/o/quizzy/.well-known/openid-configuration"
        )
        print(doc)


if __name__ == "__main__":
    a = TestOIDC()

    a.test_config()
