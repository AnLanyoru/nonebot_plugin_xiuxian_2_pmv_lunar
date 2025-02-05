import decimal


def zips(**kwargs):
    for key, value in kwargs.items():
        if isinstance(value, decimal.Decimal):
            kwargs[key] = int(value) if int(value) == value else float(value)
    return kwargs
