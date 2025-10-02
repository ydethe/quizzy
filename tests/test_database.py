from pathlib import Path
import unittest

from quizzy.__main__ import FilledQuiz, enregistre_examen
from quizzy.config import Examen


class TestDatabase(unittest.TestCase):
    def test_database(self):
        examen = Examen(
            quizz="micronutrition", email="ydethe@gmail.com", nom="de Thé", prenom="Yann"
        )
        qpth = Path(f"quizzes/{examen.quizz}.yml")
        quizz = FilledQuiz.from_yaml(qpth)
        enregistre_examen(examen, quizz, "127.0.0.1")


if __name__ == "__main__":
    a = TestDatabase()

    a.test_database()
