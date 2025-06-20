UNIVERSITY_SCHEMA = {
    '$jsonSchema': {
        'bsonType': 'object',
        'required': ['_id', 'name', 'institutes'],
        'properties': {
            '_id': {'bsonType': 'int'},
            'name': {'bsonType': 'string'},
            'address': {'bsonType': ['string', 'null']},
            'founded_date': {'bsonType': ['string', 'null']},
            'institutes': {
                'bsonType': 'array',
                'items': {
                    'bsonType': 'object',
                    'required': ['institute_id', 'name', 'departments'],
                    'properties': {
                        'institute_id': {'bsonType': 'int'},
                        'name': {'bsonType': 'string'},
                        'departments': {
                            'bsonType': 'array',
                            'items': {
                                'bsonType': 'object',
                                'required': ['department_id', 'name'],
                                'properties': {
                                    'department_id': {'bsonType': 'int'},
                                    'name': {'bsonType': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
