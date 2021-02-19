#import sys
#import os
#sys.path.append(os.path.abspath("./package"))
import requests
import json
import csv
from datetime import datetime,timedelta
import time
#from multiprocessing import Process
from bs4 import BeautifulSoup
#import math
import re
#import traceback
#from ratelimit import limits, sleep_and_retry
from scraphelper import call_limited_api
#import logging
#from time import sleep
#import random
#import urllib
from urllib.parse import quote

def get_container_html(html,tag,attr_name,attr_value):
    soup = BeautifulSoup(html,"html.parser")
    container_arr = soup.findAll( tag , { attr_name : attr_value } )
    temp_html = ''
    for temp_item in container_arr:
        temp_html += str(temp_item)
    return temp_html

def get_prop_details(html,dict_result):
    soup = BeautifulSoup(html, 'html.parser')
    temp_price = get_container_html(html,'div','class','xome-value-estimate')
    if temp_price:
        temp_price = re.sub(r'<[^>]*>', '', str(temp_price),flags=re.S|re.M)
        temp_price = re.sub(r'[^\d\.]', '', str(temp_price),flags=re.S|re.M)
        if temp_price:
            temp_price=int(temp_price.strip())
            temp_price="$"+format(temp_price,",")
            dict_result["xome_price"] = temp_price
            return temp_price
        else:
            dict_result["xome_price"] = None
            return None


def getSearchAddress(propertyAddress):
    url='https://www.xome.com/Include/AJAX/MapSearch/GetLocations.aspx?listingsonly=false&publicpropertiesonly=false&q=' + quote(propertyAddress) + '&limit=1&type=' + quote('uspscity,uspszip,county,school district,neighborhood,subdivision,middle school,elementary school, high school,mls #,') + '*address'
    responseData = None
    for i in range(1,5):
        responseData = call_limited_api(url=url, custom_headers={}, useScrapestack=False, useScrapeApi = True, retry_counter_custom=5)
        if responseData is not None:
            if responseData.text == '[]':
                #print('other try..')
                time.sleep(3)
            else:
                break
        else:
            return False


    if responseData is not None:
        #print('Response:'+str(responseData.text))
        user_datas = responseData.json()
        if len(user_datas):
            if "ListingId" in user_datas[0].keys():
                listingId = user_datas[0]["ListingId"]
                if listingId:
                    url = "https://www.xome.com/homes-for-sale/{}-{}?hv=1".format(re.compile("[^0-9a-zA-Z]", re.IGNORECASE).sub("-", propertyAddress), str(listingId))
                    return url
            elif "ListingIds" in user_datas[0].keys() and user_datas[0]["ListingIds"]:
                listingId = None
                if len(user_datas[0]["ListingIds"]):
                    listingId = user_datas[0]["ListingIds"][0]
                    if listingId:
                        url = "https://www.xome.com/homes-for-sale/{}-{}?hv=1".format(re.compile("[^0-9a-zA-Z]", re.IGNORECASE).sub("-", propertyAddress), str(listingId))
                        return url
            elif "PropertyId" in user_datas[0].keys():
                listingId = user_datas[0]["PropertyId"]
                if listingId:
                    url = "https://www.xome.com/realestate/{}-{}?hv=1".format(re.compile("[^0-9a-zA-Z]", re.IGNORECASE).sub("-", propertyAddress), str(listingId))
                    return url
    return False


def getXomeSingleProperty(searchString,dict_final):
    searchString=",".join(searchString.split(",")[:3])
    url = getSearchAddress(searchString)
    print("URL:",url)
    if url:
        print("Property url:"+url)
        dict_final['xome_url'] = url
        for i in range(1,5):
            res = call_limited_api(url=url, useScrapestack=False, useScrapeApi = True)
            if res.status_code == 200:
                try:
                    html = res.content
                    price=get_prop_details(html,dict_final)
                except Exception as e:
                    pass
            break
