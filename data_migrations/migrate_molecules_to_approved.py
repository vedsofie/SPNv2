from chat_server import db
from models.molecule import Molecule

molecules = Molecule.query.all()
for molecule in molecules:
    molecule.Approved = True
db.session.commit()
