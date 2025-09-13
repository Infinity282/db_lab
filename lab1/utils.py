def has_all_required_fields(data, required_fields):
    return all(field in data for field in required_fields)
