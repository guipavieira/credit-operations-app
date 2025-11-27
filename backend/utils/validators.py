def validate_credit_amount(amount):
    if amount <= 0:
        raise ValueError("Credit amount must be greater than zero.")
    return True

def validate_interest_rate(interest_rate):
    if interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")
    return True

def validate_credit_application(data):
    if 'amount' not in data or 'interest_rate' not in data:
        raise ValueError("Credit application must include 'amount' and 'interest_rate'.")
    validate_credit_amount(data['amount'])
    validate_interest_rate(data['interest_rate'])
    return True