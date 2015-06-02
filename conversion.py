#!/usr/bin/env python

import argparse
import json
import re
import sys
import time

from alfred import ScriptFilterList, ScriptFilterListItem
from openexchangerates import OpenExchangeRates as API


API_KEY_FILE = 'apikey'
CURRENCY_CACHE = 'currencies.json'
RATES_CACHE = 'latest.json'
RATES_FRESHNESS = 6 * 60 * 60  # 6 hours
EXIT_UNSUPPORTED = 3
EXIT_SUCCESS = 0


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
    def __read_key():
        with open(API_KEY_FILE, 'r') as f:
            key = f.read().strip()
            return key

    @staticmethod
    def __is_fresh(data_ts, freshness):
        now = time.time()
        delta = now - data_ts
        return delta < freshness


class QueryParser(object):
    @staticmethod
    def parse(query):
        result = re.search('^ *(\d+(\.\d{1,2})?) +(...) +(as|in|to) +(...) *$',
                           query)
        if not result:
            return {
                'status': 'unsupported_query',
            }

        amount = float(result.group(1))
        base = result.group(3)
        target = result.group(5)

        conv = Conversion()
        conv_result = conv.convert(amount, base, target)
        if conv_result['status'] != 'success':
            conv_result['status'] = 'unsupported_currency'
        return conv_result


def handle_alfred(args):
    qp = QueryParser()
    result = qp.parse(args.query)
    if result['status'] == 'success':
        print(make_alfred_conversion_result(result['target_amount'],
              result['base'], result['target']))
    else:
        print(make_alfred_invalid_query_result())


def make_alfred_conversion_result(result, base, target):
    retval = ScriptFilterList()
    conv_result = ScriptFilterListItem(valid=True, arg=result)
    conv_result.add_title('{} {}'.format(str(result), target))
    conv_result.add_subtitle('Action this item to copy this number to the '
                             'clipboard')
    conv_result.add_icon('icon.png')
    retval.add_item(conv_result)
    return retval


def make_alfred_invalid_query_result():
    retval = ScriptFilterList()
    item = ScriptFilterListItem(valid=False)
    item.add_title('...')
    item.add_subtitle('Please enter a valid conversion query')
    item.add_icon('icon.png')
    retval.add_item(item)
    return retval


def handle_cli(args):
    rates = Conversion()
    result = rates.convert(args.amount, args.base, args.target)
    print(result['target_amount'])
    if result['status'] != 'success':
        sys.exit(EXIT_UNSUPPORTED)
    else:
        sys.exit(EXIT_SUCCESS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Alfred and CLI tool to convert currencies using the '
        'OpenExchangeRates API.')
    parser.set_defaults(handler=None)
    subparsers = parser.add_subparsers()

    # Natural Language
    alfred_parser = subparsers.add_parser('alfred',
                                          help='Parse natural language query')
    alfred_parser.add_argument('query', type=str,
                               help='The natural language query to run.')
    alfred_parser.set_defaults(handler=handle_alfred)

    # CLI
    cli_parser = subparsers.add_parser('convert', help='Invoke in CLI mode.')
    cli_parser.add_argument('amount', type=float,
                            help='The amount to convert.')
    cli_parser.add_argument('base', type=str,
                            help='Base currency of the conversion.')
    cli_parser.add_argument('target', type=str,
                            help='Target currency.')
    cli_parser.set_defaults(handler=handle_cli)

    args = parser.parse_args()
    if args.handler:
        args.handler(args)
    else:
        print(parser.format_help())
