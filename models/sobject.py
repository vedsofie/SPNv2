import datetime
import modules.database
db = modules.database.get_db()

class SObject(object):
    def __init__(self, **kwargs):
        actual_columns, self._non_attribute_columns = self.filter_columns(**kwargs)
        db.Model.__init__(self, **kwargs)

    def filter_columns(self, **kwargs):
        actual_columns = {}
        non_column_attributes = {}
        columns = [c.name for c in self.__table__.columns]
        for key in kwargs:
            value = kwargs[key]
            if key in columns:
                actual_columns[key] = value
            else:
                non_column_attributes[key] = value
        return actual_columns, non_column_attributes

    def merge_fields(self, **fields):
        columns = self.get_all_columns()
        exceptions = []
        for col in columns:
            if col in fields:
                col = str(col)
                field_val = fields[col]
                try:
                    setattr(self, col, field_val)
                except AssertionError as e:
                    exceptions.append({"field": col, "message": str(e)})
        if len(exceptions) > 0:
            raise ValidationException(exceptions)

    def to_hash(self):
        columns = self.get_columns()
        dictionary = self.__dict__
        hash_dict = {}
        for key in columns:
            if key in dictionary:
                value = dictionary[key]
                if isinstance(value, datetime.datetime):
                    hash_dict[key] = int(value.strftime('%s'))*1000
                else:
                    hash_dict[key] = value
        return hash_dict

    @property
    def Name(self):
        table_name = self.__table__.name
        return "Lookup To %s" % table_name

    def get_columns(self):
        columns = self.get_all_columns()
        columns = set(columns) - set(self.exclude_columns)
        columns = list(columns)
        return columns

    def get_all_columns(self):
        data = self.get_column_info()
        columns = data.keys()
        return columns

    def get_column_info(self):
        meta = {c.name: SObject.get_column_details(c) for c in self.__table__.columns}
        return meta

    @staticmethod
    def get_column_details(column):
        data = {}

        data['type'] = str(column.type)
        data['name'] = column.name
        data['primary_key'] = column.primary_key

        if len(column.foreign_keys) > 0:
            data['references'] = column.foreign_keys.pop().column.table.name
        return data

    def basic_query(self, search_text):
        """resp = [{
            "name": "Test",
            "url": "/probe/1",
            "id": 1
        }]
        """
        return []

    @property
    def exclude_columns(self):
        return []

    @property
    def sfdc_lookups(self):
        return {}
        #Key->Field Name
        #Value->{'sObjectType': 'sObject', 'QueryFields': 'optional_comma_sep_fields', 'FilterField': 'optional_where_field_to_filter_on'}
        #return {"SFDC_ID": {"sObjectType": "Account"}}

    @property
    def polymorphic_lookups(self):
        return {}

    @property
    def random_color_fields(self):
        return set()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def can_save(self, userid):
        return True

class ValidationException(Exception):
    def errors(self):
        return self.args[0]

class NoPermissionException(Exception):
    pass
