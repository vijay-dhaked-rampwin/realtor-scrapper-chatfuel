import sys
import os
import time

from multiprocessing import Process
from scraphelper import call_limited_api
from selenium.common.exceptions import NoSuchElementException
import re
import urllib.parse
from bs4 import BeautifulSoup
import json
import datetime


def get_prop_details(html,prop_dict):
    #dict_result = prop_dict['prop_data']
    m = re.search(r'<script[^>]+id=hdpApolloPreloadedData[^>]*>(.+?)<\/script>', str(html),re.S | re.M | re.I)
    price=None
    if m:
        temp_html = m.group(1)
        temp_html.replace('\\','')
        json_dict_temp = json.loads(temp_html)
        if 'apiCache' in json_dict_temp and json_dict_temp['apiCache']:
            json_dict = json.loads(json_dict_temp['apiCache'])
            for key_temp in json_dict:
                temp_inner_dict = json_dict[key_temp]
                zip_temp = None
                if 'property' in temp_inner_dict and temp_inner_dict['property']:
                    dict_property = temp_inner_dict['property']
                    if 'zestimate' in dict_property and dict_property['zestimate']:
                        price=dict_property['zestimate']
    return "$"+format(price,",")

def search_price_for_address(address, dict_final):
    headers = {
        'authority':'www.zillow.com',
        'upgrade-insecure-requests':'1',
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site':'same-origin',
        'sec-fetch-mode':'navigate',
        'sec-fetch-user':'?1',
        'sec-fetch-dest':'document',
        'referer':'https://www.zillow.com/',
        'accept-language':'en-US,en;q=0.9'
    }
    address = re.sub(r'\s+', '-', address,flags=re.S|re.M)
    url = 'https://www.zillow.com/homes/'+address+'_rb'
    res = call_limited_api(url=url, custom_headers=headers,useScrapestack=False, reqMethod='GET',useScrapeApi = True)
    if res:
        prop_html = res.text
        try:
            price=get_prop_details(prop_html,dict_final)
            dict_final['zillow_price']=price
            dict_final['zillow_url']=url
            if not price:
                dict_final['zillow_price']=None
        except Exception as e:
            pass
