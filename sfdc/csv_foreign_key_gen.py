import csv

def map_primary_keys(original_primary_key_file, new_primary_key_file):
    primary_key = get_primary_key(original_primary_key_file)
    new_primary_keys = get_primary_key(new_primary_key_file)
    assert len(primary_key) == len(new_primary_keys), "The files must have the same number of rows to do this."
    keys = {}
    for i in xrange(0, len(primary_key)):
        original_key = primary_key[i]
        new_key = new_primary_keys[i]
        keys[original_key] = new_key

    print 'keys are: %s' % keys
    return keys

def get_primary_key(csv_file):
    primary_key = "Id"
    primary_keys = []
    with open(csv_file, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for col in row:
                value = row[col]
                if col == primary_key:
                    primary_keys.append(value)
    return primary_keys

def swap_foreign_keys_for(file_name, primary_keys, replacement_keys):
    new_file_name = 'new-' + file_name
    with open(file_name, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        header = reader.fieldnames
        with open(new_file_name, 'w') as new_file:
            writer = csv.DictWriter(new_file, fieldnames=header)
            writer.writeheader()
            for row in reader:
                for replace_key in replacement_keys:
                    original_key = row[replace_key]
                    new_key = primary_keys[original_key]
                    row[replace_key] = new_key
                writer.writerow(row)

def file_to_change(csv_file, new_csv_file_name):
    with open(csv_file, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)

        import pdb
        pdb.set_trace()
        for row in reader:
            for col in row:
                print col
                print row[col]
            #detection = row['Method of detection']

primary_keys = map_primary_keys("product2.csv", "uploaded_products.csv")
swap_foreign_keys_for("add_on_products.csv", primary_keys, ["Product__c", "Product_Parent__c"])
swap_foreign_keys_for("breakdown_products__c.csv", primary_keys, ["Product__c", "ParentProduct__c"])
swap_foreign_keys_for("pbes.csv", primary_keys, ["Product2Id"])

"""
swap_foreign_keys_for("add_on_products.csv")
"""


