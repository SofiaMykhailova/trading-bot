import urllib
import time
import json
import hmac
import hashlib
import requests


class ScriptError(Exception):
    pass


class ScriptQuitCondition(Exception):
    pass


API_KEY = 'here should be your key'
API_SECRET = b'here should be your secret  key'
API_URL = 'api.exmo.com'
API_VERSION = 'v1'
STOCK_TIME_OFFSET = 0


def call_api(api_method, **kwargs):

    payload = {'nonce': int(round(time.time()*1000))}

    if kwargs:
        payload.update(kwargs)

    payload = urllib.parse.urlencode(payload)

    H = hmac.new(key=API_SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()


    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": API_KEY,
               "Sign": sign}
   

    try:
        url = "https://api.exmo.com/"+API_VERSION + "/" + api_method
        response = requests.post(
            url, data=payload, headers=headers, timeout=60)
        
        if response.status_code is not 200:
            raise requests.RequestException("Server error")
        data = response.json()
     
        return data
    except requests.exceptions.ConnectTimeout:
        print('Oops. Connection timeout occured!')
    except requests.ConnectionError:
        print('Oops. Connection error')
    except requests.RequestException:
        print("Server returned error!")

