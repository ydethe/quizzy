from pathlib import Path
import unittest

from quizzy.Quiz import Quiz


class TestQuizzy(unittest.TestCase):
    def test_read_example_quiz(self):
        quiz = Quiz.from_yaml(Path("quizzes/example.yml"))
        print(quiz)

    def test_read_micronutrition_quiz(self):
        quiz = Quiz.from_yaml(Path("quizzes/micronutrition.yml"))
        print(quiz)


if __name__ == "__main__":
    a = TestQuizzy()

    a.test_read_example_quiz()
    a.test_read_micronutrition_quiz()
