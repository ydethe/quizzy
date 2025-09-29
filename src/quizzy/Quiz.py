from pathlib import Path
from typing import Dict, List, Optional, Set
import json

import yaml
from yaml import BaseLoader
from pydantic import BaseModel


class Question(BaseModel):
    text: str
    answers: List[str]
    good_answers: List[int]
    user_answers: Set[int] = set()

    @property
    def number_of_answers(self) -> int:
        return len(self.answers)


class Quiz(BaseModel):
    name: Optional[str] = ""
    message_accueil: str
    text_bouton: str
    questions: List[Question]
    # echelle_scores: List[Dict[int,str]]
    echelle_scores: Dict[int, str]

    @property
    def number_of_questions(self) -> int:
        return len(self.questions)

    @classmethod
    def from_yaml(cls, yml_pth: Path):
        with open(yml_pth, "r") as f:
            dat = yaml.load(f, Loader=BaseLoader)
        quiz = cls.model_validate_json(json.dumps(dat))
        quiz.name = yml_pth.stem
        return quiz
