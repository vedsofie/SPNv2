from chat_server import db
from models.sequence import Sequence

sequences = Sequence.query.all()
for sequence in sequences:
    if sequence.MadeOnElixys:
        sequence.SynthesisModule = 'SOFIE ELIXYS'
    else:
        sequence.SynthesisModule = 'Other'
    db.session.add(sequence)

db.session.commit()