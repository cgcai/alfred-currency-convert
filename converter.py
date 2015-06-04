#!/usr/bin/env python

import argparse
import re
import sys

from lib.alfred import ScriptFilterList, ScriptFilterListItem
from lib.currency import Conversion


API_KEY_FILE = 'apikey'

# Used when run in CLI mode.
EXIT_UNSUPPORTED = 3
EXIT_SUCCESS = 0


class APIKeyError(Exception):
    pass


class App(object):
    def __init__(self):
        try:
            self.__api_key = App.__read_key()
        except IOError:
            raise APIKeyError

    def handle_alfred(self, args):
        result = self.execute_query(args.query)
        print(result)

    def handle_cli(self, args):
        rates = Conversion()
        result = rates.convert(args.amount, args.base, args.target)
        print(result['target_amount'])
        if result['status'] != 'success':
            sys.exit(EXIT_UNSUPPORTED)
        else:
            sys.exit(EXIT_SUCCESS)

    def execute_query(self, query):
        match_handlers = [
            # Tuples of the form (handler, regex), evaluated sequentially.
            (self.__query_autocomplete_preposition,
                '^ *(\d+(\.\d{1,2})?) +(...) *$'),
            (self.__query_explicit,
                '^ *(\d+(\.\d{1,2})?) +(...) +(as|in|to) +(...) *$')
        ]

        # If a match is found, execute its handler and return.
        for handler, regex in match_handlers:
            match_result = re.search(regex, query)
            if match_result:
                return handler(match_result)

        # Otherwise, return a generic unsupported query result.
        return App.__invalid_query_result()

    def __query_explicit(self, match_result):
        amount = float(match_result.group(1))
        base = match_result.group(3)
        target = match_result.group(5)

        conv = Conversion(self.__api_key)
        conv_result = conv.convert(amount, base, target)
        return App.__conversion_result(conv_result['target_amount'],
                                       conv_result['base'],
                                       conv_result['target'])

    def __query_autocomplete_preposition(self, match_result):
        query = match_result.group(0).strip()
        return App.__autocomplete_preposition_result(query)

    @staticmethod
    def __read_key():
        with open(API_KEY_FILE, 'r') as f:
            key = f.read().strip()
            return key

    @staticmethod
    def __autocomplete_preposition_result(query):
        suggestion = query + ' to '

        retval = ScriptFilterList()
        item = ScriptFilterListItem(valid=False, autocomplete=suggestion)
        item.add_title('convert {}...'.format(suggestion[:-1]))
        item.add_subtitle('Action this item to autocomplete')
        item.add_icon('icon.png')
        retval.add_item(item)
        return retval

    @staticmethod
    def __conversion_result(result, base, target):
        retval = ScriptFilterList()
        conv_result = ScriptFilterListItem(valid=True, arg=result)
        conv_result.add_title('{} {}'.format(str(result), target))
        conv_result.add_subtitle('Action this item to copy this number to the '
                                 'clipboard')
        conv_result.add_icon('icon.png')
        retval.add_item(conv_result)
        return retval

    @staticmethod
    def __invalid_query_result():
        retval = ScriptFilterList()
        item = ScriptFilterListItem(valid=False)
        item.add_title('...')
        item.add_subtitle('Start by typing an amount')
        item.add_icon('icon.png')
        retval.add_item(item)
        return retval


if __name__ == '__main__':
    app = App()

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
    alfred_parser.set_defaults(handler=app.handle_alfred)

    # CLI
    cli_parser = subparsers.add_parser('convert', help='Invoke in CLI mode.')
    cli_parser.add_argument('amount', type=float,
                            help='The amount to convert.')
    cli_parser.add_argument('base', type=str,
                            help='Base currency of the conversion.')
    cli_parser.add_argument('target', type=str,
                            help='Target currency.')
    cli_parser.set_defaults(handler=app.handle_cli)

    args = parser.parse_args()
    if args.handler:
        args.handler(args)
    else:
        print(parser.format_help())
