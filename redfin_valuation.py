import sys
import os
sys.path.append(os.path.abspath("./package"))
import time
import logging
from multiprocessing import Process
from scraphelper import call_limited_api
from selenium.common.exceptions import NoSuchElementException
import re
import urllib.parse
from bs4 import BeautifulSoup
import json
import datetime

def get_prop_details(html,dict_result):
    m = re.search(r'>\s*MLS#<\/span>(.+?)<\/span>', str(html),re.S | re.M | re.I)
    if m:
        mls_no = m.group(1)
        mls_no = re.sub(r'<.*?>', '', mls_no,flags=re.S|re.M)

    s=html.find('@type":"Offer","priceCurrency":"USD","price":')
    e=html.find(',"url":',s)
    m=html[s+len('@type":"Offer","priceCurrency":"USD","price":'):e]
    if m:
        price = int(m.strip())
        return "$"+format(price,",")

def search_price_for_address(address, dict_final):
    url = 'https://www.redfin.com/stingray/do/avm/location-autocomplete?'+ urllib.parse.urlencode({
        "location" : address
    })
    print(url)
    proxy = {}
    headers = {'authority':'www.redfin.com',
            'upgrade-insecure-requests':'1',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site':'none',
            'sec-fetch-mode':'navigate',
            'sec-fetch-user':'?1',
            'sec-fetch-dest':'document',
            'accept-language':'en-US,en;q=0.9',
            'cookie': 'RF_BROWSER_ID=a6c1preBSJu3GxMbXZSPGw; RF_BID_UPDATED=1; _gcl_au=1.1.1648166767.1593594192; RF_BROWSER_CAPABILITIES=%7B%22screen-size%22%3A4%2C%22ie-browser%22%3Afalse%2C%22events-touch%22%3Afalse%2C%22ios-app-store%22%3Afalse%2C%22google-play-store%22%3Afalse%2C%22ios-web-view%22%3Afalse%2C%22android-web-view%22%3Afalse%7D; _fbp=fb.1.1593594194640.350140682; G_ENABLED_IDPS=google; _ga=GA1.2.1806903516.1593594204; RF_VISITED=true; ki_r=; userPreferences=parcels%3Dtrue%26schools%3Dfalse%26mapStyle%3Ds%26statistics%3Dtrue%26agcTooltip%3Dfalse%26agentReset%3Dfalse%26ldpRegister%3Dfalse%26afCard%3D2%26schoolType%3D0%26lastSeenLdp%3DnoSharedSearchCookie; RF_UNBLOCK_ID=vQ3P3zOT; _gid=GA1.2.743126021.1594057139; unifiedLastSearch=name%3D3211%2520Chippewa%2520St%26subName%3DNew%2520Orleans%252C%2520LA%26url%3D%252FLA%252FNew-Orleans%252F3211-Chippewa-St-70115%252Fhome%252F79447497%26id%3D9_79447497%26type%3D9%26isSavedSearch%3D%26countryCode%3DUS; RF_CORVAIR_LAST_VERSION=321.4.0; RF_MARKET=socal; RF_BUSINESS_MARKET=3; RF_LAST_SEARCHED_CITY=San%20Diego; ki_t=1593774191054%3B1594097736925%3B1594119488042%3B2%3B4; _uetsid=319f5251-aeb1-0f8f-3f2d-63220d87362e; _uetvid=6283ec94-58e2-decd-98f9-d9ce53f5b807; RF_LDP_VIEWS_FOR_PROMPT=%7B%22viewsData%22%3A%7B%2207-03-2020%22%3A%7B%22120312592%22%3A3%2C%22120315611%22%3A1%2C%22120321779%22%3A1%7D%2C%2207-04-2020%22%3A%7B%22121605892%22%3A1%7D%2C%2207-06-2020%22%3A%7B%22120321779%22%3A1%7D%2C%2207-07-2020%22%3A%7B%22120321779%22%3A2%2C%22121322260%22%3A1%2C%22121721529%22%3A1%2C%22121745503%22%3A3%2C%22121775533%22%3A2%7D%7D%2C%22expiration%22%3A%222022-07-03T10%3A27%3A14.385Z%22%2C%22totalPromptedLdps%22%3A0%7D; RF_LISTING_VIEWS=121721529.121775533.121745503.121322260.120321779.121605892.120312592.120315611; AKA_A2=A',
        }
    res = call_limited_api(url=url, custom_headers=headers, useScrapestack=False,reqMethod='GET',useScrapeApi=True)
    if res:
        html = res.text
        m = re.search(r'"url":"(.+?)"', html)
        if m:
            property_url = 'https://www.redfin.com'+m.group(1)
            print("property url",property_url)
            res = call_limited_api(url=property_url, custom_headers=headers, useScrapestack=False,reqMethod='GET',useScrapeApi=True)
            if res:
                prop_html = res.text
                try:
                    price=get_prop_details(prop_html,dict_final)
                    dict_final['redfin_price']=price
                    dict_final['redfin_url']=property_url
                    if not price:
                        dict_final['redfin_price']=None
                except Exception as e:
                    pass
            else:
                print('could not get url for:'+property_url)
    else:
        print('could not get the html for url:'+url)
