from pathlib import Path
from typing import List
import json

import yaml
from yaml import BaseLoader
from pydantic import BaseModel


class Question(BaseModel):
    text: str
    answers: List[str]
    good_answers: List[int]

    @property
    def number_of_answers(self) -> int:
        return len(self.answers)


class Quiz(BaseModel):
    questions: List[Question]

    @property
    def number_of_questions(self) -> int:
        return len(self.questions)

    @classmethod
    def from_yaml(cls, yml_pth: Path) -> "Quiz":
        with open(yml_pth, "r") as f:
            dat = yaml.load(f, Loader=BaseLoader)
        quiz = Quiz.model_validate_json(json.dumps(dat))
        return quiz
