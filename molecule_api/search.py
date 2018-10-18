import requests

def find_matches(chem_name):
    res = requests.get('http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/%s/cids/JSON?name_type=word' % chem_name)
    res = res.json()
    try:
        matches = res['IdentifierList']['CID']
        matches = [str(match) for match in matches]
        matches = matches[0:10]
        res = requests.get('http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IUPACName/JSON' % ','.join(matches))
        matches = res.json()
        return matches
    except:
        return []

def get_common_names(cids):
    url = 'http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/description/JSON' % ','.join(cids)
    res = requests.get(url)
    return res.json()

def get_descriptions(cids):
    url = 'http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/%s/description/JSON' % ','.join(cids)
    res = requests.get(url)
    return res.json()

def species_list():
    res = requests.get('http://www.reactome.org/ReactomeRESTfulAPI/RESTfulWS/speciesList', headers={'Accept': 'application/json'})
    return res.json()

def species_pathway_hierarchy(species):
    res = requests.get('http://www.reactome.org/ReactomeRESTfulAPI/RESTfulWS/pathwayHierarchy/%s' % species, headers={'Accept': 'application/xml'})
    return res

if __name__ == "__main__":
    pass
