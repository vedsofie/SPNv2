import base64
import io
import zipfile
import os
import json

import modules.database
db = modules.database.get_db()


from sequence import Sequence
from component import Component
from statuslog import StatusLog
from sequenceattachment import SequenceAttachment


def update_components(sequence_id, sequence_data):
    sequence_file, status_log_file, attachments = None, None, []
    try:
        zip_data = io.BytesIO(sequence_data)
        sequence_zipped = zipfile.ZipFile(zip_data)
        sequence_file, status_log_file, attachments = parse_zipped_sequence_structure(sequence_zipped)
    except zipfile.BadZipfile:
        sequence_file = sequence_data

    try:
        imported_sequence = json.loads(sequence_file)
        comps = Component.do_import(imported_sequence, sequence_id)
    except ValueError:
        raise SequenceImportException("The .sequence file is corrupted")


def do_import(sequence_data, owner_id, data):
    sequence_file, status_log_file, attachments = None, None, []
    try:
        zip_data = io.BytesIO(sequence_data)
        sequence_zipped = zipfile.ZipFile(zip_data)
        sequence_file, status_log_file, attachments = parse_zipped_sequence_structure(sequence_zipped)
    except zipfile.BadZipfile:
        sequence_file = sequence_data

    try:
        seq = import_sequence_file(sequence_file, owner_id, data)

        import_attachments(attachments, seq.SequenceID)
        import_status_logs(status_log_file, seq.SequenceID)
        return seq.SequenceID
    except ValueError:
        raise SequenceImportException("The .sequence file is corrupted")


def import_status_logs(status_log_file, sequence_owner_id):
    if status_log_file:
        statuses = json.loads(status_log_file)
        for status in statuses:
            log = StatusLog(StatusString=json.dumps(status), SequenceID=sequence_owner_id)
            db.session.add(log)
        db.session.commit()


def import_attachments(attachments, sequence_owner_id):
    for attachment in attachments:
        attachment.SequenceID = sequence_owner_id
        db.session.add(attachment)
    db.session.commit()


def import_sequence_file(sequence_file, owner_id, data):
    imported_sequence = json.loads(sequence_file)
    imported_sequence['sequence']['userid'] = owner_id
    seq = Sequence.do_import(imported_sequence,data)
    comps = Component.do_import(imported_sequence, seq.SequenceID)
    return seq


def parse_zipped_sequence_structure(sequence_zipped):
    attachments = []
    status_log_file = None
    sequence_file = None

    for file_name in sequence_zipped.namelist():
        directories = os.path.split(file_name)
        if file_name.endswith(".sequence") and len(directories) == 2:# and directories[1] == file_name:
            sequence_file = sequence_zipped.read(file_name)
        elif file_name.endswith(".status_log") and len(directories) == 2:# and directories[1] == file_name:
            status_log_file = sequence_zipped.read(file_name)
        else:
            if len(directories) > 0 and directories[0] == "instructions":
                attachment = SequenceAttachment()
                attachment.FileName = os.path.basename( file_name )
                attachment.Attachment = sequence_zipped.read(file_name)
                attachments.append( attachment )
    if not sequence_file: raise SequenceImportException("The zip file must contain a .sequence file to be imported")
    return (sequence_file, status_log_file, attachments)

class SequenceImportException(Exception):
    def __init__(self, msg=''):
        super(SequenceImportException, self).__init__(msg)

