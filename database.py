from chat_server import db

from sqlalchemy.sql.expression import join, select, table, column, alias
from models.user import User
from models.sequence import Sequence
from models.labsystem import LabSystem
from models.molecule import Molecule
from models.comment import Comment
from models.sequenceattachment import SequenceAttachment

if "__main__" == __name__:
  session = db.session()
  from IPython import embed
  embed()
