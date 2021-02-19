from scraphelper import call_limited_api
import re
import urllib.parse
from bs4 import BeautifulSoup
import json

def get_prop_details(html,dict_result):
	price=None
	try:
		li_html = html.find("span",attrs={"class":"jsx-4285822472 price"})
		price= li_html.text
	except:
		pass
	return price

def search_price_for_address(property_row, dict_final):
	dict_final['realtor_price']=None
	headers = {
			'authority':'www.realtor.com',
			'cache-control':'no-cache',
			'upgrade-insecure-requests':'1',
			'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
			'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'sec-fetch-site':'none',
			'sec-fetch-mode':'navigate',
			'sec-fetch-user':'?1',
			'sec-fetch-dest':'document',
			'accept-language':'en-US,en;q=0.9'
		}
	url="https://parser-external.geo.moveaws.com/search?client_id=rdc-x&"+urllib.parse.urlencode({"input":property_row})
	data='{}'
	p_res = call_limited_api(url=url,custom_headers=headers,useScrapestack=False, reqMethod='GET', postData=data,useScrapeApi = True)
	property_row="-".join("_".join(i.strip() for i in property_row.split(",")).split())
	print(p_res)
	if p_res:
		html = p_res.text
		html=json.loads(html)
		if 'hits' in html and html['hits']:
			if html['hits'][0]:
				if 'mpr_id' in html['hits'][0] and html['hits'][0]['mpr_id']:
					m="M"+html['hits'][0]['mpr_id']
					headers = {
							'authority':'www.realtor.com',
							'cache-control':'max-age=0',
							'upgrade-insecure-requests':'1',
							'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
							'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
							'sec-fetch-site':'none',
							'sec-fetch-mode':'navigate',
							'sec-fetch-user':'?1',
							'sec-fetch-dest':'document',
							'accept-language':'en-US,en;q=0.9'
						}
					property_url = 'https://www.realtor.com/realestateandhomes-detail/' + property_row +"_"+m
					print("property_url",property_url)
					p_res = call_limited_api(url=property_url, custom_headers=headers, reqMethod='GET',useScrapeApi=True)
					print(p_res)
					dict_final['realtor_url']=property_url
					if p_res:
						soup = BeautifulSoup(p_res.text, 'html.parser')
						price=get_prop_details(soup,dict_final)
						print(price)
						dict_final['realtor_price']=price
