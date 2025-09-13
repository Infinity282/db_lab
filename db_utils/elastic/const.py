SETTINGS = {
    "analysis": {
        "analyzer": {
            "russian": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                        "stop",
                        "snowball"
                ]
            }
        },
        "filter": {
            "russian_stop": {
                "type": "stop",
                "stopwords": "_russian_"
            },
            "russian_stemmer": {
                "type": "snowball",
                "language": "Russian"
            }
        }
    }
}
INDEX_NAME = "class_materials"
MAPPINGS = {
    "properties": {
        "material_id": {"type": "integer"},
        "content": {
            "type": "text",
            "analyzer": "russian",
            "fields": {"keyword": {"type": "keyword"}}
        },
        "class_id": {"type": "integer"},
    }
}
