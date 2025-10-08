import uuid


def generate_transactions_ref(code = "TXN"):
    """
    Generate a unique booking reference using UUID4.
    Format: BK-<YYYYMMDD>-<first10chars of uuid4>
    """
    token = uuid.uuid4().hex[:10].upper()
    return f"{code}-{token}"