import unittest

from quizzy.config import Examen
from quizzy.crypto import encrypt_payload, decrypt_payload


class TestCrypto(unittest.TestCase):
    def test_aes(self):
        data = "jhfdjhfdjéSyrd 123!"
        cipher = encrypt_payload(data)
        decipher = decrypt_payload(cipher)

        self.assertEqual(decipher, data)

    def test_etudiant(self):
        e = Examen(quizz="micronutrition", email="ydethe@gmail.com", nom="de Thé", prenom="Yann")

        m = e.get_encrypted()
        print(m)

        e2 = Examen.from_encrypted(m)

        self.assertEqual(e.quizz, e2.quizz)
        self.assertEqual(e.email, e2.email)
        self.assertEqual(e.prenom, e2.prenom)
        self.assertEqual(e.nom, e2.nom)


if __name__ == "__main__":
    a = TestCrypto()

    a.test_aes()
    a.test_etudiant()
