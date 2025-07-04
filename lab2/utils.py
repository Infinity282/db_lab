def has_all_required_fields(data, required_fields):
    if not all(field in data for field in required_fields):
        return False
    return True