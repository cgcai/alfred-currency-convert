import json
import time

from openexchangerates import OpenExchangeRates as API


API_KEY_FILE = 'apikey'
CURRENCY_CACHE = 'currencies.json'
RATES_CACHE = 'latest.json'
RATES_FRESHNESS = 6 * 60 * 60  # 6 hours


class APIKeyError(Exception):
    pass


class Conversion(object):
    def __init__(self):
        try:
            self.__api_key = Conversion.__read_key()
        except IOError:
            raise APIKeyError

        self.__api = API(self.__api_key)

    def __refresh_currencies(self):
        currencies = self.__api.currencies()
        with open(CURRENCY_CACHE, 'w') as f:
            json.dump(currencies, f, indent=2, sort_keys=True)
        return currencies

    def __refresh_rates(self):
        rates = self.__api.latest()
        with open(RATES_CACHE, 'w') as f:
            json.dump(rates, f, indent=2, sort_keys=True)
        return rates

    def supported_currencies(self):
        currencies = None
        try:
            with open(CURRENCY_CACHE, 'r') as f:
                currencies = json.load(f)
        except IOError:
            currencies = self.__refresh_currencies()
        return currencies

    def __get_rates(self):
        rates = None
        try:
            with open(RATES_CACHE, 'r') as f:
                rates = json.load(f)
        except IOError:
            rates = self.__refresh_rates()

        if not Conversion.__is_fresh(rates['timestamp'], RATES_FRESHNESS):
            rates = self.__refresh_rates()

        return rates['rates']

    def convert(self, amount, base, target):
        base = base.upper()
        target = target.upper()

        rates = self.__get_rates()

        # Check if conversion is supported.
        if base not in rates or target not in rates:
            return {
                'status': 'not_supported',
                'result': '-1'
            }

        # Convert 'amount' to USD.
        # (The free OpenExchangeRates API restricts base currency to USD)
        if base != 'USD':
            amount /= rates[base]

        # Convert a USD amount to the target currency.
        result = amount * rates[target]
        return {
            'status': 'success',
            'result': result
        }

    @staticmethod
    def __read_key():
        with open(API_KEY_FILE, 'r') as f:
            key = f.read().strip()
            return key

    @staticmethod
    def __is_fresh(data_ts, freshness):
        now = time.time()
        delta = now - data_ts
        return delta < freshness


def main():
    pass

if __name__ == '__main__':
    main()
