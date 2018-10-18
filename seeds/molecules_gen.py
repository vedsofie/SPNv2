import generate_db
from models.molecule import Molecule, db
from models.keyword import Keyword
import csv
import re
import requests
import time

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

unique = set()
pets = []
substances = []
with open('micad.csv', 'rb') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        detection = row['Method of detection']
        if "PET" in detection or "pet" in detection or "positron emission tomography" in detection:
            unique.add(detection)
            if row["Pubchem Link(s)"]:
                matches = re.match(".*?sid=([0-9]*).*", row["Pubchem Link(s)"])
                if matches:
                    substance_id = matches.group(1)
                    substances.append(substance_id)
                    row['substance_id'] = substance_id
                    pets.append(row)

all_subs = ",".join(substances)
resp = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/%s/cids/JSON?cids_type=all" % all_subs)
json = resp.json()
cids = []
missing = []
alternatives = {}
for info in json["InformationList"]["Information"]:
    if "CID" in info:
        cid = info["CID"][0]
        cids.append(cid)
        if len(info["CID"]) > 0:
            alternatives[cid] = []
            for alt_cid in info["CID"][1:]:
                alternatives[cid].append(alt_cid)
    else:
        missing.append(info)
print "Missing Count: %i" % len(missing)

cids = [str(cid) for cid in cids]


objs = {}
for chunk in chunks(cids, 10):
    url = "http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/description/JSON" % ",".join(chunk)
    resp = requests.get(url)
    info = resp.json()['InformationList']["Information"]
    print info
    for obj in info:
        objs[obj["CID"]] = {
            "Name": obj["Title"],
            "DisplayFormat": obj["Title"],
            "CID": obj["CID"]
        }
    time.sleep(1)

for my_cids in chunks(objs.keys(), 10):
    local_cids = [str(cid) for cid in my_cids]
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/property/MolecularFormula/JSON" % ",".join(local_cids)
    res = requests.get(url)
    res = res.json()
    for prop in res['PropertyTable']['Properties']:
        cid = prop["CID"]
        objs[cid]["Formula"] = prop["MolecularFormula"]
    time.sleep(1)


for key in objs.keys():
    obj = objs[key]
    try:
        mole = Molecule(**obj)
        mole.save()
    except:
        db.session.rollback()
        print 'failed to save'

### Get Molecule Images
moles = Molecule.query.all()

"""
for mole in moles:
    mole.save_image_from_pubchem()
    print 'saving image'
    time.sleep(1)
"""

mapped_moles = {str(mole.CID): mole for mole in moles}
for chunk in chunks(mapped_moles.keys(), 10):
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/synonyms/JSON" % ','.join(chunk)
    resp = requests.get(url)
    pubchem_info = resp.json()['InformationList']['Information']
    for info in pubchem_info:
        cid = info['CID']
        if "Synonym" in info:
            for syn in info['Synonym']:
                mole = mapped_moles[str(cid)]
                syn = syn[0:299]
                print syn
                key = Keyword(Type='Molecules', \
                              ParentID=mole.ID, \
                              Keyword=syn, \
                              Category='Synonym', \
                              DisplayFormat=syn)
                db.session.add(key)
    db.session.commit()




#http://www.nirs.go.jp/research/division/mic/db/eng/mplsearch.php?target=target_null&nuclide=nuclide_all&compound=&keyword=