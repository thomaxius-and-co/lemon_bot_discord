from datetime import datetime


VALID_COINS = ['BTC', 'ETH', 'LTC', 'XLM']


def is_float(arg) -> bool:
    try:
        return isinstance(float(arg), float)
    except ValueError:
        return False


def is_positive(arg) -> bool:
    try:
        return float(arg) > 0
    except TypeError:
        return False


def is_valid_sell_amount(arg) -> bool:
    return arg == 'max' or (is_float(arg) and is_positive(arg))


# todo: Use coin names fetched from API
def is_valid_coin(arg) -> bool:
    return arg.upper() in VALID_COINS


def is_valid_date(arg) -> bool:
    try:
        return isinstance(datetime.strptime(arg, '%Y-%m-%d'), datetime)
    except ValueError:
        return False


def validate(expected_arguments: dict, args: dict):
    validation_result = {}
    for arg_key, arg_value in args.items():
        arg_validators, is_required, error_message = expected_arguments.get(arg_key).values()
        if is_required and arg_value is None:
            validation_result.update({arg_key: f"Argument: {arg_key} missing"})
            continue
        elif not is_required and arg_value is None:
            continue
        for validator in arg_validators:
            is_valid = validator(arg_value)
            if not is_valid:
                validation_result.update({arg_key: error_message})
                break
    return ValidationResult(validation_result)


class ValidationResult:

    def __init__(self, result_per_arg: dict):
        self.result_per_arg = result_per_arg or {}

    @property
    def is_valid(self):
        if self.result_per_arg is None:
            raise Exception('Error: validation not run')
        return len(self.result_per_arg) == 0

    def as_messages(self):
        if self.result_per_arg is None:
            raise Exception('Error: validation not run')
        return self.result_per_arg.values()




EXPECTED_ARGUMENTS = {
    'rtb_transaction': {
        'price': {
            'validators': [
                is_float,
                is_positive,
            ],
            'required': True,
            'error_message': 'Price needs to be a positive number'
        },
        'amount_sell': {
            'validators': [
                is_valid_sell_amount,
            ],
            'required': True,
            'error_message': "Sell amount needs to be a positive number or 'max'"
        },
        'amount_buy': {
            'validators': [
                is_float,
                is_positive,
            ],
            'required': True,
            'error_message': "Buy amount needs to be a positive number"
        },
        'coin': {
            'validators': [
                is_valid_coin,
            ],
            'required': True,
            'error_message': f"Coin name needs to be one of {','.join(VALID_COINS)}"
        },
        'date': {
            'validators': [
                is_valid_date,
            ],
            'required': False,
            'error_message': 'Date needs to be in format YYYY-MM-DD'
        }
    }
}