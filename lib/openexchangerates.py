import requests


class OpenExchangeRates(object):
    __base_url = 'http://openexchangerates.org/api'

    def __init__(self, api_key):
        self.__api_key = api_key

    def __del__(self):
        pass

    def currencies(self):
        url = '{base}/currencies.json?app_id={app_id}'.format(
            base=OpenExchangeRates.__base_url, app_id=self.__api_key)

        # TODO: no network/http error status codes
        r = requests.get(url)
        return r.json()

    def latest(self, base_currency='USD'):
        url = '{base}/latest.json?base={currency}&app_id={app_id}'.format(
            base=OpenExchangeRates.__base_url, currency=base_currency,
            app_id=self.__api_key)

        # TODO: no network/http error status codes
        r = requests.get(url)
        return r.json()

    # TODO: implement
    # def historical(self, year, month, day):
    #    pass
