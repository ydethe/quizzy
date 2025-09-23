import unittest

from quizzy.read_quiz import read_quiz


class TestQuizzy(unittest.TestCase):
    def test_read_quiz(self):
        read_quiz()


if __name__ == "__main__":
    a = TestQuizzy()

    a.test_read_quiz()
