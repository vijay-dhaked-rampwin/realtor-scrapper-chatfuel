#import sys
#import os
#sys.path.append(os.path.abspath("./package"))
#import time
#import logging
#from multiprocessing import Process
from scraphelper import call_limited_api
#from selenium.common.exceptions import NoSuchElementException
import re
import json
import datetime


def search_price_for_address(address, dict_result):
    dict_result['chase_url']="https://valuemap.corelogic.com/ValuemapResponsive.aspx?licenseCode=57ab486697a44315b843ba02f220a342"
    dict_result['chase_price'] =None
    url = 'https://valuemap.corelogic.com/ValueMapService.asmx/GetPropertyInfoReport'
    proxy = {}

    headers = {
      'Connection': 'keep-alive',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/json; charset=UTF-8',
      'Accept': '*/*',
      'Origin': 'https://valuemap.corelogic.com',
      'Sec-Fetch-Site': 'same-origin',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Dest': 'empty',
      'Referer': 'https://valuemap.corelogic.com/ValuemapResponsive.aspx?licenseCode=57ab486697a44315b843ba02f220a342',
      'Accept-Language': 'en-US,en;q=0.9',
    }
    data = '{"licenseCode":"57ab486697a44315b843ba02f220a342","Address":"' + str(address) + '","propertyType":"","numBeds":0,"numBaths":0,"numTotalRooms":0,"livingArea":0,"yearBuilt":0,"currentValue":0,"languageCode":"en-US","renderPropListHTML":true,"requestType":"New","leadNumber":"0"}'
    res = call_limited_api(url, custom_headers=headers,useScrapestack=False, reqMethod='POST', postData=data,useScrapeApi=True, retry_counter_custom=3)
    if res:
        html = res.text
        try:
            json_data = json.loads(html)
            if 'd' in json_data and json_data['d']:
                if 'SubjectProperty' in json_data['d'] and json_data['d']['SubjectProperty']:
                    if 'DisplayPrice' in json_data['d']['SubjectProperty'] and json_data['d']['SubjectProperty']['DisplayPrice']:
                        price= int(str(json_data['d']['SubjectProperty']['DisplayPrice']).strip())
                        price="$"+format(price,",")
                        dict_result['chase_price'] =price

        except Exception as e:
            print('Exception occured..'+str(e))
    else:
        print('could not get data:')
