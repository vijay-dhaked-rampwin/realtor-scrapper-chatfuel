#import sys
#import os
#sys.path.append(os.path.abspath("./package"))
#import time
#import logging
#from multiprocessing import Process
from scraphelper import call_limited_api
#from selenium.common.exceptions import NoSuchElementException
import re
#import urllib.parse
from bs4 import BeautifulSoup
import json
#import datetime

def search_price_for_address(address, dict_final):
    dict_final['forsalebyowner_price'] =None

    headers = {
        'Accept':'application/json, text/plain, */*',
        'Referer':'https://www.forsalebyowner.com/sell-my-house/pricingscout/avm',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        }
    url = 'https://directory.forsalebyowner.com/google-suggestions?query='+str(address)
    res = call_limited_api(url=url, custom_headers=headers, useScrapestack=False,reqMethod='GET',useScrapeApi=True)
    print(url)
    dict_final['forsalebyowner_url']="https://www.forsalebyowner.com/"
    if res:
        html = res.text
        json_dict = json.loads(html)
        if 'suggestions' in json_dict and json_dict['suggestions']:
            if 'details' in json_dict['suggestions'][0] and json_dict['suggestions'][0]['details']:
                dict_details = json_dict['suggestions'][0]['details']
                if 'prices_middle' in dict_details and dict_details['prices_middle'] and dict_details['prices_middle'] != "0":
                    price= int(str(dict_details['prices_middle']).strip())
                    price="$"+format(price,",")
                    dict_final['forsalebyowner_price'] =price
    else:
        print('could not get the html for url:'+url)
