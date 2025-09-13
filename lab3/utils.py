from datetime import datetime


def has_all_required_fields(data, required_fields):
    return all(field in data for field in required_fields)


def get_date_range(year: str, semester: int):
    """
    Преобразует год и семестр в диапазон дат.
    :param year: Год (целое число или строка, преобразуемая в число).
    :param semester: Номер семестра (1 или 2).
    :return: Кортеж (start_date, end_date) — строки в формате 'YYYY-MM-DD'.
    """
    try:
        year = int(year)
        if semester == 1:
            start_date = f"{year}-09-01"
            end_date = f"{year}-12-31"
        elif semester == 2:
            start_date = f"{year+1}-01-01"
            end_date = f"{year+1}-06-30"
        else:
            raise ValueError("Invalid semester: must be 1 or 2")
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
        return start_date, end_date
    except ValueError as e:
        raise ValueError(f"Invalid date parameters: {str(e)}")
