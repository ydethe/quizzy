from datetime import datetime
from pathlib import Path
from pony.orm import Database, Required, PrimaryKey, Set


db = Database()


class Session(db.Entity):
    id = PrimaryKey(int, auto=True)
    quiz_nom = Required(str)
    quiz_hash = Required(str)
    etudiant_id = Required("Etudiant")
    date = Required(datetime)
    reponses = Required(str)
    score = Required(float)
    ip_origine = Required(str)


class Etudiant(db.Entity):
    id = PrimaryKey(int, auto=True)
    nom = Required(str)
    prenom = Required(str)
    sessions = Set(Session)
    email = Required(str)


db_pth = Path("quizzes") / "quizzy.sqlite"
db.bind(provider="sqlite", filename=str(db_pth.absolute()), create_db=True)
db.generate_mapping(create_tables=True)
