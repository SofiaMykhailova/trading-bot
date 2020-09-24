
import urllib
import urllib.request
import json
import requests


class ScriptQuitCondition(Exception):
    pass



def get_pair_settings(pair):
    response = requests.get("https://api.exmo.com/v1.1/pair_settings")
    data = response.json()

    if pair in data:
        pair_settings = data[pair]
        return PairSettings(pair_settings['price_precision'], pair_settings['min_quantity'])

    raise ScriptQuitCondition(F'Can not find  pair_settings for{pair}')


class PairSettings:
    def __init__(self, price_precision, min_quantity):
        self.__price_precision = price_precision
        self.__min_quantity = min_quantity
       

    @property
    def price_precision(self):
        return self.__price_precision
    
    @property
    def min_quantity(self):
        return self.__min_quantity
