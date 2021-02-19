#import sys
#import os
#sys.path.append(os.path.abspath("./package"))
#import requests
import json
#import csv
#from datetime import datetime,timedelta
#import time
#from multiprocessing import Process
from bs4 import BeautifulSoup
#import math
import re
#import traceback
from selenium import webdriver
from ratelimit import limits, sleep_and_retry
from scraphelper import call_limited_api
#import logging
import urllib.parse

def getMellisaData(propertyData,dict_final):
	propertyData=propertyData.split(",")
	dict_final['mellisa_price']=None
	retryCounter = 0

	url = "https://www.melissa.com/v2/lookups/property/?" + urllib.parse.urlencode({
        "address": propertyData[0].strip(),
        "city" : propertyData[1].strip(),
        "state" : propertyData[2].strip().split()[0],
        "zip" : propertyData[2].strip().split()[1]
    })

	print(url)
	dict_final['mellisa_url']=url

	while retryCounter < 10:
		html = call_limited_api(url, useScrapeApi=True, custom_headers={
			"Referer" : "https://www.melissa.com/v2/lookups/property/",
			"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
			"Host": "www.melissa.com",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "same-origin",
			"Sec-Fetch-User": "?1",
			"Upgrade-Insecure-Requests": "1"
		})

		if html.status_code == 200:
			print('Fetch Success for Mellisa')
			try:
				soup = BeautifulSoup(html.text, 'html.parser')
				mainDataTable = soup.find('tbody')
				if mainDataTable is None:
					errorField = soup.find('span',attrs={"class" : "red-text"})
					if errorField is not None and re.match('^\(YE.*', errorField.text.strip(), re.IGNORECASE | re.DOTALL):
						print(errorField.text)
						break
					elif errorField is not None:
						print(errorField.text)

				else:
					assessmentYear = None
					for eachRow in mainDataTable.findAll("tr", recursive=False):
						allTd = eachRow.findAll('td', recursive=False)
						if len(allTd) == 2:
							fieldName = (allTd[0].text).strip()
							fieldValue = (allTd[1].text).strip()
							if re.match('.*Estimated Market Value.*', fieldName, re.IGNORECASE | re.DOTALL):
								price = int(re.sub("[^0-9]", "", fieldValue).strip())
								price="$"+format(price,",")
								dict_final['mellisa_price']=price
								return

					break
			except Exception as e:
				pass
		else:
			print("Property Not found on Melisa")
		retryCounter += 1
		print("Retrying Melisa")
