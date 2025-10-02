import hashlib
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
    token: Optional[str] = ""
    message_accueil: str
    text_bouton: str
    questions: List[Question]
    echelle_scores: Dict[int, str]

    @property
    def number_of_questions(self) -> int:
        return len(self.questions)

    @classmethod
    def from_yaml(cls, yml_pth: Path):
        with open(yml_pth, "r") as f:
            dat = yaml.load(f, Loader=BaseLoader)
        quiz = cls.model_validate_json(json.dumps(dat))
        return quiz

    @property
    def hash(self) -> str:
        m = hashlib.sha256()
        raw = self.model_dump_json().encode("utf-8")
        m.update(raw)
        return m.hexdigest()
