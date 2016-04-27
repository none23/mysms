#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Copyright (c) 2015 Nick Anisimov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import argparse
import requests
from os import getenv


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-id", dest="api_id", metavar="VALUE",
                        help="API ID (optional)")
    parser.add_argument("--to", metavar="PHONENUMBER",
                        help="Telephone number to send the message to (req'd)")
    parser.add_argument("--message", metavar="MESSAGE", type=str,
                        help="Message to be sent (by default read from stdin")
    parser.add_argument("--from", dest="sendername", metavar="VALUE",
                        help="Sender name (optional)")
    parser.add_argument("--wait", metavar="VALUE",
                        help="Wait given number of minutes before sending")
    parser.add_argument("--time", metavar="VALUE",
                        help="Send at certain time (UNIX_TIME) (optional)")
    parser.add_argument("--translit", action="store_true",
                        help="Convert to latin")
    parser.add_argument("--debug", action="store_true",
                        help="Debug mode: simulate sending (free of charge)")
    args = parser.parse_args()
    return args


def check_args_type(func):
    def inner(args=None):
        if isinstance(args, argparse.Namespace):
            return func(args)
        else:
            print(("The argument to <" + str(func.__name__) +
                   "> needs to be an argparce.Namespace, got " +
                   str(type(args).__name__)) + ".")
            return None
    return inner


def argparse_to_url_keys(args):
    """ Creates a dict of url parameters from an argparse.Namespace.
    Returns a dict to be used as 'params' value of a requests.get() object.
    """
    url_keys = dict()
    api_id = get_api_id(args)
    phone_number = get_phone_number(args)
    message = get_message(args)
    if api_id is None:
        print("Failed to get api-id.")
        sys.exit(1)
    if phone_number is None:
        print("Failed to get phone number.")
        sys.exit(1)
    if message is None:
        print("Failed to get the massage text.")
        sys.exit(1)
    url_keys['api_id'] = api_id
    url_keys['to'] = phone_number
    url_keys['text'] = message
    if args.debug:
        url_keys['test'] = '1'
    if args.sendername:
        url_keys['from'] = args.sendername
    if args.time:
        url_keys['time'] = parse_arg_time(args.time)
    return url_keys


def parse_arg_time(input_value):
    if isinstance(input_value, str):
        try:
            # date and time given
            input_date, input_time = input_value.split('')
            try:
                input_hh, input_mm = input_time.split(':')
            except ValueError:
                # incorrect input_value
                print('failed to parse the value of time')
                sys.exit(1)
        except ValueError:
            # only time given
            try:
                input_hh, input_mm = input_value.split(':')
            except ValueError:
                # incorrect input_value
                print('failed to parse the value of time')
                sys.exit(1)


@ check_args_type
def get_api_id(args):
    if args.api_id:
        api_id = args.api_id
    else:
        try:
            with open("%s/.smssendrc" % (getenv('HOME'))) as fp:
                data = fp.read()
        except IOError as errstr:
            print(errstr)
            sys.exit(3)
        if len(data) >= 10:
            api_id = data.replace("\r\n", "")
            api_id = api_id.replace("\n", "")
    return str(api_id)


@ check_args_type
def get_phone_number(args):
    if args.to:
        phone_number = args.to
    else:
        try:
            with open("%s/.mynumber" % (getenv('HOME'))) as f:
                phone_number = str(f.read())
        except IOError as errstr:
            print(errstr)
            sys.exit(3)
        phone_number = phone_number.replace("\r\n", "")
        phone_number = phone_number.replace("\n", "")
    return str(phone_number)


def set_url_keys(message, debug=False, phone_number=get_phone_number(),
                 time=None, sendername=None, api_id=get_api_id()):
    """ Converts arguments to url parameters dict """

    url_keys = dict()
    url_keys['api_id'] = api_id
    url_keys['to'] = phone_number
    url_keys['text'] = message
    if debug:
        url_keys['test'] = '1'
    if sendername:
        url_keys['from'] = sendername
    if time:
        url_keys['time'] = time
    return url_keys


@ check_args_type
def get_message(args):
    if args.message:
        message = args.message
    else:
        print("Type in the message, and press C-d to send it")
        message = sys.stdin.read()
    return message


def make_request(url_keys):
    """ Makes an HTTP GET request with the parameters passed in (as a dict)
    Returns a translation of the response received (as a str)
    """
    if not isinstance(url_keys, dict):
        print(("The argument to <make_request> needs to be a dict, got " +
               str(type(url_keys).__name__) + "."))
        sys.exit(1)
    if 'api_id' in url_keys and 'text' in url_keys and 'to' in url_keys:
        http_get = requests.get("http://sms.ru/sms/send", params=url_keys)
        response = http_get.text
        response = response.split('\n')[0]
        result = translate_response(response)
    else:
        result = "The argument misses one or more required keys"
    return result


def translate_response(code):
    """ Translates response status codes into meaningful strings"""
    if not isinstance(code, int):
        try:
            code = int(code)
        except:
            raise Exception("arg must be an int (%s given)" % (type(code)))

    servicecodes = {
        100: "Message sent successfully",
        200: "Incorrect api_id",
        201: "Low account balance",
        202: "Incorrect recipient specified",
        203: "Massage has no text",
        204: "Sender name not approved",
        205: "Message too long",
        206: "Daily message limit reached",
        207: "Can send messages to this number",
        208: "Incorrect value of 'time'",
        209: "You have added this number to stop-list",
        210: "Need to use a POST request (GET request used)",
        211: "Method not found",
        220: "Service currently unavailable; try again later",
        }
    if code in servicecodes.keys():
        meaning = servicecodes[code]
    else:
        meaning = "Undocumented response code: %s" % code
    return meaning


if __name__ == "__main__":
    args = parse_args()
    url_keys = argparse_to_url_keys(args)
    result = make_request(url_keys)
    print(result)
