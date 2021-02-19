#import sys
#import os
#sys.path.append(os.path.abspath("./package"))
#import time
#import logging
#from multiprocessing import Process
from scraphelper import call_limited_api
#from selenium.common.exceptions import NoSuchElementException
import re
import urllib.parse
from bs4 import BeautifulSoup
import json
#import datetime
#import traceback;


def search_price_for_address(address, dict_final):
    dict_final["eppraisal_price"]=None
    url = 'https://www.eppraisal.com/lk?' + urllib.parse.urlencode({
		"address" : address
	})
    print(url)
    res = call_limited_api(url=url, useScrapeApi = True)
    print(res)
    if res:
        prop_html = res.text
        soup = BeautifulSoup(prop_html, "html.parser")
        #print(soup)
        pageTitle = soup.find( 'h1' , { 'class' : 'title' } )
        if pageTitle.text == "Property Not Found":
            pass
        else:
            try:
                dict_final["eppraisal_url"] = res.headers["sa-final-url"]
                mainContainer = soup.find( 'table' , { 'class' : 'prop_details' } )
                if mainContainer:
                    eppraisalImgLogo = mainContainer.find('img', {'alt' : "Eppraisal Logo"});
                    if eppraisalImgLogo:
                        epprDataNode = eppraisalImgLogo.parent;
                        homeValueNode = epprDataNode.find( 'h3' , { 'epp_field' : '' } )
                        if homeValueNode and homeValueNode.text != 'n/a':
                            dict_final["eppraisal_price"]=homeValueNode.text


            except Exception as e:
                pass
