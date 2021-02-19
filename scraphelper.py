import requests
import json
import csv
import time
import re
from time import sleep
import pymysql
import mysql.connector
from Config import Config,password,username,hostname
obj_config = Config()

def getConnection():
	return mysql.connector.connect(host=obj_config.host,
								user=obj_config.db_user,
								password=obj_config.db_password,
								db=obj_config.database)

def Send_estimation_request_data_Data(req_id):
	mydb=getConnection()
	mycursor=mydb.cursor()
	mycursor.execute(f''' select source,estimate_value,url from estimation_request_data where request_id={req_id}''')
	all_prices=mycursor.fetchall()
	mycursor.close()
	mydb.close()
	return all_prices

def AddToestimation_requests(raw_address,full_address,status,user_id,source):
	mydb=getConnection()
	mycursor=mydb.cursor()
	mycursor.execute(f''' insert into estimation_requests (raw_address,full_address,
	status,user_id,source) values ("{raw_address}","{full_address}",{status},
	"{user_id}","{source}")''')
	req_id=mycursor.lastrowid
	mydb.commit()
	mycursor.close()
	mydb.close()
	return req_id

def UpdateToestimation_requests(req_id):
	mydb=getConnection()
	mycursor=mydb.cursor()
	mycursor.execute(f''' update estimation_requests set status=2 where id={req_id}''')
	mydb.commit()
	mycursor.execute(f''' select user_id from estimation_requests where id={req_id}''')
	user_id=mycursor.fetchall()
	mycursor.close()
	mydb.close()
	return user_id

def AddToestimation_request_data(url,req_id,source,e_value):
	e_value=e_value[1:]
	e_value=int(e_value.replace(',',''))
	mydb=getConnection()
	mycursor=mydb.cursor()
	mycursor.execute(f''' insert into estimation_request_data (url,request_id,source,
	estimate_value) values ("{url}",{req_id},"{source}",{e_value})''')
	mydb.commit()
	mycursor.close()
	mydb.close()

def scrapeApi(url, headers={},postData={},reqMethod=None):
	from scraper_api import ScraperAPIClient
	client = ScraperAPIClient('670c69fe8adc1cc48d2ed687e3da7b4b')
	if reqMethod == 'POST':
		api_result = client.post(url = url, headers=headers, body = postData)
		return api_result
	else:
		api_result = client.get(url=url, headers=headers)
		return api_result
	return None

headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36"};

def call_limited_api(url, custom_headers={}, useScrapestack=False, reqMethod='GET', postData={}, useScrapeApi = False, retry_counter_custom=0):
	retry_counter_count = 15
	retryCounter = 0
	response = None
	failure = True
	if reqMethod == "POST":
		requestFunc = requests.post
	else:
		requestFunc = requests.get

	if retry_counter_custom > 0:
		retry_counter_count = retry_counter_custom
	while retryCounter < retry_counter_count:
		try:
			if useScrapeApi or useScrapestack:
				response = scrapeApi(url=url, headers=custom_headers,postData=postData,reqMethod=reqMethod)
			else:
				proxy, user_agent = getProxyDict()
				custom_headers.update(headers)
				response = requestFunc(url, timeout=15, headers=custom_headers, proxies=proxy, data=postData)

			if response.status_code == 429:
				time.sleep(3)
				continue
			elif (useScrapeApi == True and response.status_code != 200 and response.status_code != 404) or  (response.status_code != 200 and useScrapeApi == False) or re.match('.*Please complete the CAPTCHA below.*', response.text, re.IGNORECASE | re.DOTALL):
				time.sleep(3+retryCounter)
				retryCounter += 1
				if retryCounter > 3 and useScrapestack == True:
					useScrapestack = False
					useScrapeApi = True
			else:
				failure = False
				break
		except Exception as e:
			time.sleep(1+retryCounter)
			retryCounter += 1
	return response
