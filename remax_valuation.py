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
from urllib.parse import quote

"""logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

process_thread_count = 30
settingParams = getApplicationSettings()
if settingParams is not None:
    process_thread_count = int(settingParams['process_thread_count'])
"""

def search_price_for_address(sended_address, dict_result):
    citystatezip=",".join(sended_address.split(",")[1:])
    address=sended_address.split(",")[0]
    headers = {'Connection':'keep-alive',
    'Accept':'application/json, text/plain, /',
    'Origin':'https://www.remax.com',
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
    'Content-Type':'application/json;charset=UTF-8',
    'Sec-Fetch-Site':'cross-site',
    'Sec-Fetch-Mode':'cors',
    'Referer':'https://www.remax.com/home-value-estimates',
    'Accept-Encoding':'gzip, deflate, br',
    'Accept-Language':'en-GB,en-US;q=0.9,en;q=0.8',
    }
    data = '{"autocompleteValue":"'+str(address)+'","categories":["addresses"],"sort":{}}'
    res_1 = call_limited_api(url='https://public-api-gateway-prod.kube.remax.booj.io/listings/autocomplete', custom_headers=headers,useScrapestack=False, reqMethod='POST', postData=data,useScrapeApi = True)
    if res_1:
        json_text = res_1.text
        json_dict = json.loads(json_text)
        #print(json_dict)
        if 'addresses' in json_dict and json_dict['addresses']:
            #print(type(json_dict['addresses']))
            #print(json_dict['addresses'])
            if 'uPI' in json_dict['addresses'][0] and json_dict['addresses'][0]['uPI']:
                upi = str(json_dict['addresses'][0]['uPI'])
            else:
                return
        else:
            return
    url="https://www.remax.com/"+sended_address.split(",")[2].strip().split()[0]+"/"+"-".join(sended_address.split(",")[1].strip().split())+"/home-details/"+"-".join("-".join(i.split()) for i in sended_address.split(","))+"/"+upi
    print(url)
    res = call_limited_api(url=url, custom_headers={}, useScrapestack=False,useScrapeApi = True)
    dict_result['remax_url']=url
    if res:
        html = res.text
        try:
            s=html.find('<h4 class="md:text-right')
            e=html.find('</h4>',s)
            sub=str(html)[s:e]
            s=sub.find("$")
            if s==-1:
                dict_result['remax_price']=None
                return
            price=sub[s:]
            price=price.strip()
            dict_result['remax_price']=price

        except Exception as e:
            print('Exception occured..'+str(e))
    else:
        print('could not get data:')
