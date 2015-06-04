import json
import time

from openexchangerates import OpenExchangeRates as API


CURRENCY_CACHE = 'currencies.json'
RATES_CACHE = 'latest.json'
RATES_FRESHNESS = 6 * 60 * 60  # 6 hours


class Conversion(object):
    def __init__(self, api_key, currency_cache=CURRENCY_CACHE,
                 rates_cache=RATES_CACHE, rates_freshness=RATES_FRESHNESS):
        self.__api_key = api_key
        self.__currency_cache = currency_cache
        self.__rates_cache = rates_cache
        self.__rates_freshness = rates_freshness

        self.__api = API(self.__api_key)

    def __refresh_currencies(self):
        currencies = self.__api.currencies()
        with open(self.__currency_cache, 'w') as f:
            json.dump(currencies, f, indent=2, sort_keys=True)
        return currencies

    def __refresh_rates(self):
        rates = self.__api.latest()
        with open(self.__rates_cache, 'w') as f:
            json.dump(rates, f, indent=2, sort_keys=True)
        return rates

    def supported_currencies(self):
        currencies = None
        try:
            with open(self.__currency_cache, 'r') as f:
                currencies = json.load(f)
        except IOError:
            currencies = self.__refresh_currencies()
        return currencies

    def __get_rates(self):
        rates = None
        try:
            with open(self.__rates_cache, 'r') as f:
                rates = json.load(f)
        except IOError:
            rates = self.__refresh_rates()

        if not Conversion.__is_fresh(rates['timestamp'],
                                     self.__rates_freshness):
            rates = self.__refresh_rates()

        return rates['rates']

    def convert(self, amount, base, target):
        base = base.upper()
        target = target.upper()

        rates = self.__get_rates()

        retval = {
            'base_amount': amount,
            'base': base,
            'target': target
        }

        # Check if conversion is supported.
        if base not in rates or target not in rates:
            retval['status'] = 'unsupported'
            retval['target_amount'] = -1
            return retval

        # Convert 'amount' to USD.
        # (The free OpenExchangeRates API restricts base currency to USD)
        if base != 'USD':
            amount /= rates[base]

        # Convert a USD amount to the target currency.
        result = amount * rates[target]
        retval['status'] = 'success'
        retval['target_amount'] = result
        return retval

    @staticmethod
    def __is_fresh(data_ts, freshness):
        now = time.time()
        delta = now - data_ts
        return delta < freshness
