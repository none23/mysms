#!/usr/bin/env python3
# -*- coding: utf8 -*-

# This is a slightly changed version of smssend by Denis Khabarov
# Originally from https://github.com/dkhabarov/smssend


import sys
import argparse
import httplib2
from os import getenv
from urllib.parse import quote

parser = argparse.ArgumentParser(
    epilog="""
    Return codes:
        0 - Message send successful
        1 - Service has retured error message
        2 - HTTP Error
        3 - Error for usage this tool
    Default API ID are read from the files:
        Linux: $HOME/.smssendrc
        Windows: %USERPROFILE%/.smssendrc
    Example usage:
        echo "Hello world" | smssend --api-id=youapiid --to=target_phone_number
    """,
    description="""
    smssend is a program to send SMS messages from the commandline.
    Using API service http://sms.ru
    """,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    prog="smssend",
    usage="%(prog)s --help"
            )
parser.add_argument("--api-id", dest="api_id", metavar="VALUE",
                    help="API ID (optional)")
parser.add_argument("--to", metavar="PHONENUMBER",
                    help="Telephone number to send the message to (required)")
parser.add_argument("--message", metavar="MESSAGE",
                    help="Message to be sent (by default read from stdin")
parser.add_argument("--from", dest="sendername", metavar="VALUE",
                    help="Sender name (optional)")
parser.add_argument("--time", metavar="VALUE",
                    help="Send time using UNIX TIME format (optional)")
parser.add_argument("--translit", action="store_true", help="Convert to latin")
parser.add_argument("--debug", action="store_true",
                    help="Print debug messages")
cliargs = parser.parse_args()

servicecodes = {
    100: "Сообщение принято к отправке. На следующих строчках  вы найдете \
          идентификаторы отправленных сообщений в том же порядке, в котором \
          вы указали номера, на которых совершалась отправка.",
    200: "Неправильный api_id",
    201: "Не хватает средств на лицевом счету",
    202: "Неправильно указан получатель",
    203: "Нет текста сообщения",
    204: "Имя отправителя не согласовано с администрацией",
    205: "Сообщение слишком длинное (превышает 8 СМС)",
    206: "Будет превышен или уже превышен дневной лимит на отправку сообщений",
    207: "На этот номер (или один из номеров) нельзя отправлять сообщения, \
          либо указано более 100 номеров в списке получателей",
    208: "Параметр time указан неправильно",
    209: "Вы добавили этот номер (или один из номеров) в стоп-лист",
    210: "Используется GET, где необходимо использовать POST",
    211: "Метод не найден",
    220: "Сервис временно недоступен, попробуйте чуть позже.",
    300: "Неправильный token (возможно истек срок действия, \
          либо ваш IP изменился)",
    301: "Неправильный пароль, либо пользователь не найден",
    302: "Пользователь авторизован, но аккаунт не подтвержден (пользователь \
          не ввел код, присланный в регистрационной смс)",
    }


def show_debug_messages(msg):
    if cliargs.debug:
        print(msg)


def get_home_path():
    if sys.platform.startswith('freebsd') or sys.platform.startswith('linux'):
        home = getenv('HOME')
    elif sys.platform.startswith('win'):
        home = getenv('USERPROFILE')
    if home:
        return home
    else:
        print("Unable to get home path.")
        sys.exit(3)


def get_api_id():
    if cliargs.api_id:
        api_id = cliargs.api_id
    else:
        try:
            with open("%s/.smssendrc" % (get_home_path())) as fp:
                data = fp.read()
        except IOError as errstr:
            print(errstr)
            sys.exit(3)
        if len(data) >= 10:
            api_id = data.replace("\r\n", "")
            api_id = api_id.replace("\n", "")
    return str(api_id)


def get_phonenumber():
    if cliargs.to:
        phonenumber = cliargs.to
    else:
        try:
            with open("%s/.mynumber" % (get_home_path())) as f:
                phonenumber = str(f.read())
        except IOError as errstr:
            print(errstr)
            sys.exit(3)
        phonenumber = phonenumber.replace("\r\n", "")
        phonenumber = phonenumber.replace("\n", "")
    return str(phonenumber)


def get_msg():
    if cliargs.message:
        message = cliargs.message
    else:
        message = sys.stdin.read()
    return message


if __name__ == "__main__":
    api_id = get_api_id()
    phonenumber = get_phonenumber()
    if api_id is None:
        print("Failed to get api-id. Please make sure " +
              get_home_path() + " file exists or see --help")
        sys.exit(3)
    if phonenumber is None:
        print("Failed to get api-id. Please make sure " +
              get_home_path() + " file exists or see --help")
        sys.exit(3)

    url = ("http://sms.ru/sms/send?api_id=" + api_id + "&to=" +
           phonenumber + "&text=" + quote(get_msg()) + "&partner_id=3805")
    if cliargs.debug:
        url = url + "&test=1"
    if cliargs.sendername:
        url = url + "&from=" + cliargs.sendername
    if cliargs.time:
        url = url + "&time=" + str(int(cliargs.time))
    if cliargs.translit:
        url = url + "&translit=1"

    try:
        h = httplib2.Http()
        print(url)
        response, content = h.request(url)
        show_debug_messages("GET: " + url +
                            "\nStatus:\n" + str(response.status))
    except Exception() as errstr:
        show_debug_messages("smssend[debug]: " + errstr)
        sys.exit(2)

    service_result = str(content, 'utf-8')
    if service_result:
        if int(service_result[0]) == 100:
            show_debug_messages("smssend[debug]: Message send ok. ID: " +
                                str(service_result))
            sys.exit(0)
        else:
            show_debug_messages("smssend[debug]: Unable send sms message to" +
                                phonenumber + " Service has returned code: " +
                                servicecodes[int(service_result)])
            sys.exit(1)
