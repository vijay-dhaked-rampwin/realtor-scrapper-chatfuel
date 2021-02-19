import sys;
import os;
sys.path.append(os.path.abspath("./package"))
import requests
import json
import csv
from datetime import datetime,timedelta
import time
from multiprocessing import Process
from bs4 import BeautifulSoup
import math;
import re
import traceback;
from selenium import webdriver
from ratelimit import limits, sleep_and_retry
from scraphelper import getProxyDict, writeToFile,readFile, getOneFromTable,getReRunnableOwnerRecords, getReRunnableAgentRecords, updateSetting, insertIntoTable, updateTable, getCounties, getValue, splitName, getApplicationSettings, proxyCrawler, call_limited_api
import logging
from mellisa import getMellisaData
import shutil
import uuid
import all_values

logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

timenow = datetime.now()
imagesTargetDir = os.path.dirname(os.path.abspath(__file__)) + "/../downloaded_images/" + str(timenow.year) + "/" + str(timenow.month) + "/" + str(timenow.day)
imagesBaseUrl = "/upload/" + str(timenow.year) + "/" + str(timenow.month) + "/" + str(timenow.day)

if not os.path.exists(imagesTargetDir):
    os.makedirs(imagesTargetDir)

headers = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"};

# process_thread_count_setting = getOneFromTable(['setting_value'], 'settings', 'setting_key', 'process_thread_count')
process_thread_count = 30
retry_counter_count = 25

settingParams = getApplicationSettings()
if settingParams is not None:
	process_thread_count = int(settingParams['process_thread_count'])
	retry_counter_count = int(settingParams['retry_counter'])




def getSinglePropertyData(propertyData):
	url = 'https://www.realtor.com/realestateandhomes-detail/' + propertyData["permalink"];
	print("Fetching Property " + url);
	html = call_limited_api(url, useScrapestack=True);
	if html is None:
		return;

	html = html.text;
	# writeToFile(html, "detailtest.html")

	#html = readFile("detailtest.html")

	providerJson = None;
	fullDetailsJson = None;
	try:
		soup = BeautifulSoup(html, 'html.parser')
		ogImage = soup.find("meta",  property="og:image")

		if ogImage is not None and ogImage["content"] != "":
			image_url = downloadAndSaveImage(ogImage["content"])
			updateTable("properties", "property_id", propertyData["property_id"], {
				'primary_photo' : image_url if image_url else ogImage["content"]
			})

		providerDetails = soup.find("script",  id="__NEXT_DATA__")

		if providerDetails is not None:
			providerJson = providerDetails.string
			jsonData = json.loads(providerJson);

			basicUpdateJson = {
				"full_address_display" : jsonData["props"]["pageProps"]["seoContent"]["zoho"]["meta_data"]["header_1"]
			}

			parcelNumberGroups = re.search(r"Parcel Number: ([A-Za-z0-9\-]*)", html);
			if parcelNumberGroups is not None:
				parcelNumber = parcelNumberGroups.group(1).strip();
				basicUpdateJson["parcel_number"] = parcelNumber

			# Update other details of property
			updateTable("properties", "property_id", propertyData["property_id"], basicUpdateJson)

			if "consumer_advertisers" in jsonData["props"]["pageProps"]["property"].keys():
				agentJson = {
					"posted_by" : "broker"
				}

				agent_profile_link = None
				for advNode in jsonData["props"]["pageProps"]["property"]["consumer_advertisers"]:
					if advNode["type"] == "Agent":
						agent_profile_link = advNode["href"]
						agentJson["agent_profile_link"] = agent_profile_link
						agent_name = advNode["name"]
						if agent_name is not None:
							first_name, last_name = splitName(agent_name)
							agentJson["agent_name"] = agent_name
							agentJson["agent_first_name"] = first_name
							agentJson["agent_last_name"] = last_name
					elif advNode["type"] == "Office":
						agentJson["broker_name"] = advNode["name"]
						agentJson["office_contact"] = advNode["phone"]
						#agentJson["broker_number"] = advNode["broker_id"]
						agentJson["broker_location"] = advNode["address"]["city"] + ", " + advNode["address"]["state_code"]

				# if agent_profile_link is None:
				# 	agentProfileLinkNode = soup.find('a',attrs={"data-omtag" : "ldp:listingProvider:agentProfile"})
				# 	agent_profile_link = agentProfileLinkNode.get("href") if agentProfileLinkNode is not None else None


				# "mls_id" : getValue(jsonData, 'mls_id', 'listing_provider'),
				# "mls_name" : getValue(jsonData, 'mls_name', 'listing_provider')

				print(agentJson)
				updateTable("properties", "property_id", propertyData["property_id"], agentJson)

				try:
					if agent_profile_link is not None:
						# TODO check if this is already scrapped.
						agentDetailsObj = getOneFromTable(['id'], 'agent_details', 'agent_profile_link', agent_profile_link)
						if agentDetailsObj is not None:
							# agentDetailJson = {
							# 	"agent_name" : agent_name if agent_name is not None else None,
							# 	"agent_first_name" : first_name if first_name is not None else None,
							# 	"agent_last_name" : last_name if last_name is not None else None,
							# 	"office_contact" : getValue(jsonData, 'office_contact', 'listing_provider'),
							# 	"broker_name" : getValue(jsonData, 'broker_name', 'listing_provider'),
							# 	"broker_number" : getValue(jsonData, 'broker_number', 'listing_provider'),
							# 	"broker_location" : getValue(jsonData, 'broker_location', 'listing_provider'),
							# }
							# updateTable("agent_details", "agent_profile_link", agent_profile_link ,agentDetailJson)
							print("This agent {} is already scrapped. Skipping it".format(agent_profile_link))
						else:
							url = 'https://www.realtor.com' + agent_profile_link;
							print("Agent Url " +  url)
							agenthtml = call_limited_api(url, useScrapestack=True);
							if agenthtml is None:
								print("Error in getting agent html")
								pass;
							else:
								soup = BeautifulSoup(agenthtml.content, 'html.parser');

								mainContactNode = soup.find("script",  id="__NEXT_DATA__")

								if mainContactNode is None:
									print("Main node not found")
								else:
									providerJson = mainContactNode.string
									agentJsonData = json.loads(providerJson);

									del agentJson["posted_by"]
									agentDetailJson = agentJson
									phoneNumbers = [];
									websites = [];
									phoneCounter = {
										"office" : 0,
										"mobile" : 0,
										"fax" : 0,
										"other" : 0
									}

									for eachNumberNode in agentJsonData["props"]["pageProps"]["agentDetails"]["phones"]:
										if eachNumberNode["type"] == "Mobile":
											phoneCounter["mobile"] = phoneCounter["mobile"] + 1
											if phoneCounter["mobile"] <= 3:
												agentDetailJson["agent_mobile_phone_" + str(phoneCounter["mobile"])] = eachNumberNode["number"]
										elif eachNumberNode["type"] == "Fax":
											phoneCounter["fax"] = phoneCounter["fax"] + 1
											if phoneCounter["fax"] <= 3:
												agentDetailJson["agent_fax_phone_" + str(phoneCounter["fax"])] = eachNumberNode["number"]
										elif eachNumberNode["type"] == "Office":
											phoneCounter["office"] = phoneCounter["office"] + 1
											if phoneCounter["office"] <= 3:
												agentDetailJson["agent_office_phone_" + str(phoneCounter["office"])] = eachNumberNode["number"]
										else:
											phoneCounter["other"] = phoneCounter["other"] + 1
											if phoneCounter["other"] <= 5:
												agentDetailJson["agent_other_phone_" + str(phoneCounter["other"])] = eachNumberNode["number"]

									agentDetailJson["agent_websites"] = getValue(agentJsonData["props"]["pageProps"], 'href', 'agentDetails')
									try:
										agentDetailJson["agent_websites_2"] = getValue(agentJsonData["props"]["initialReduxState"]["profile"]["agentdetail"]["agent_bio"], 'website', 'office')
										#agentDetailJson["agent_email"] = getValue(agentJsonData["props"]["initialReduxState"]["profile"]["agentdetail"]["agent_bio"], 'email', 'office')

									except Exception as e:
										pass

									agentDetailJson["agent_street"] = getValue(agentJsonData["props"]["pageProps"]["agentDetails"], 'line', 'address')
									agentDetailJson["agent_postcode"] = getValue(agentJsonData["props"]["pageProps"]["agentDetails"], 'postal_code', 'address')
									agentDetailJson["agent_locality"] = getValue(agentJsonData["props"]["pageProps"]["agentDetails"], 'city', 'address')

									state_code = getValue(agentJsonData["props"]["pageProps"]["agentDetails"], 'state_code', 'address')
									if  state_code != "":
										agentDetailJson["agent_region"] = state_code
									else:
										agentDetailJson["agent_region"] = getValue(agentJsonData["props"]["pageProps"]["agentDetails"], 'state', 'address')

									agentDetailJson["agent_address"] =  agentDetailJson["agent_street"] + ", " + agentDetailJson["agent_locality"] + ", " + agentDetailJson["agent_region"] + " " + agentDetailJson["agent_postcode"]

									if "social_media" in agentJsonData["props"]["pageProps"]["agentDetails"].keys():
										for social_media, social_media_value in agentJsonData["props"]["pageProps"]["agentDetails"]["social_media"].items():
											if social_media == "facebook":
												agentDetailJson["agent_facebook"] = social_media_value["href"]
											elif social_media == "twitter":
												agentDetailJson["agent_twitter"] = social_media_value["href"]

									print(agentDetailJson)
									insertIntoTable('agent_details', agentDetailJson);
									#updateTable("properties", "property_id", propertyData["property_id"], agentDetailJson)
					else:
						print("Agent Key not found")
				except Exception as e:
					print(e);
					logging.warning("Exception in getting agent data - " + propertyData["property_id"]);
					print(propertyData["property_id"]);
					traceback.print_exc()
			elif "new_community" in jsonData.keys():
				agent_name = getValue(jsonData["new_community"], 'brand_name', 'builder')
				first_name, last_name = splitName(agent_name)
				updateTable("properties", "property_id", propertyData["property_id"], {
					"posted_by" : "builder",
					"agent_profile_link" : getValue(jsonData["new_community"], 'site', 'builder'),
					"office_contact" : getValue(jsonData["new_community"], 'toll_free_number', 'listing_provider'),
					"agent_name" : agent_name,
					"agent_first_name" : first_name,
					"agent_last_name" : last_name,
				})

	except Exception as e:
		logging.warning("Error in getting property details");
		print(providerJson);
		print(e);
		traceback.print_exc()

def getTotalRecords(county, dayOnRealtor=1):
	url = 'https://www.realtor.com/realestateandhomes-search/' + county["county_name"] +  '/dom-1'
	print("Fetching County Data " + url);

	html = call_limited_api(url, useScrapestack=True);
	if html is None:
		return;

	soup = BeautifulSoup(html.content, 'html.parser');
	jsonData = None
	try:
		mainJson = soup.find('script',attrs={'id':'__NEXT_DATA__'});
		jsonData = json.loads(mainJson.text);
	except Exception as e:
		print(html.content)

	totalFromDom = 0
	totalCountEle = soup.find('span',attrs={'data-testid':'results-header-count'});
	if totalCountEle is not None:
		print(totalCountEle.text);
		totalFromDom = int(totalCountEle.text.split(' ')[0].replace(',', ''))

	searchResults = {
		"count" : 0,
		"total" : 0,
		"results" : []
	};

	try:
		searchResults = jsonData["props"]["pageProps"]["searchResults"]["home_search"];
		#print(searchResults)
	except Exception as e:
		traceback.print_exc()
	print(searchResults["count"], searchResults["total"])


	pageCount = int(math.ceil(totalFromDom/searchResults["count"])) if searchResults["count"] != 0 else 0
	processedResults = processCountyResults(county, searchResults) if totalFromDom > 0 else []
	return pageCount, processedResults, totalFromDom;

def getSingleCountyData(county, results = [], dayOnRealtor=1, pageNo=1):
	url = 'https://www.realtor.com/realestateandhomes-search/' + county["county_name"] +  '/dom-1' + '/pg-' + str(pageNo);
	print("Fetching County Data " + url);

	html = call_limited_api(url, useScrapestack=True);
	if html is None:
		return results;

	soup = BeautifulSoup(html.content, 'html.parser');

	jsonData = None
	try:
		mainJson = soup.find('script',attrs={'id':'__NEXT_DATA__'});
		jsonData = json.loads(mainJson.text);
	except Exception as e:
		print(html.content)


	searchResults = {
		"count" : 0,
		"results" : []
	};
	try:
		searchResults = jsonData["props"]["pageProps"]["searchResults"]["home_search"];

	except Exception as e:
		traceback.print_exc()

	print("Found Results for country" + str(searchResults["count"]));
	return processCountyResults(county, searchResults, results)

def processCountyResults(county, searchResults, results = []):
	splittedCountyName = county["county_name"].split("-County")
	extractedCountyName = splittedCountyName[0] if len(splittedCountyName) >= 1 else county["county_name"]
	actualCountyName = extractedCountyName.replace("-", ' ')
	print(actualCountyName);
	excludeList = []
	for propertyData in searchResults["results"]:
		logging.warning(propertyData["property_id"] + " " +  propertyData["permalink"] + " " +  propertyData["list_date"]);
		#print(propertyData);

		propertyCountyName = getValue(propertyData["location"], 'name', 'county')

		if propertyCountyName != actualCountyName and propertyCountyName != extractedCountyName:
			continue

		insertJson = {
			"property_id" : propertyData["property_id"],
			"county_id" : county["id"],
			"type" : getValue(propertyData, 'type', 'description'),
			"beds" : getValue(propertyData, 'beds', 'description'),
			"baths_full" : getValue(propertyData, 'baths_full', 'description'),
			"baths" : getValue(propertyData, 'baths', 'description'),
			"garage" : getValue(propertyData, 'garage', 'description'),
			"year_built" : getValue(propertyData, 'year_built', 'description'),
			"sub_type" : getValue(propertyData, 'sub_type', 'description'),
			"sqft" : getValue(propertyData, 'sqft', 'description'),
			"lot_sqft" : getValue(propertyData, 'lot_sqft', 'description'),
			"stories" : getValue(propertyData, 'stories', 'description'),
			"baths_half" : getValue(propertyData, 'baths_half', 'description'),
			"baths_3qtr" : getValue(propertyData, 'baths_3qtr', 'description'),
			"baths_1qtr" : getValue(propertyData, 'baths_1qtr', 'description'),
			"list_date" : (getValue(propertyData, 'list_date')).split("T")[0],
			"listing_id" : getValue(propertyData, 'listing_id'),
			"list_price" : getValue(propertyData, 'list_price'),
			"permalink" : getValue(propertyData, 'permalink'),
			"county" : getValue(propertyData["location"], 'name', 'county'),
			"state_code" : getValue(propertyData["location"], 'state_code', 'address'),
			"postal_code" : getValue(propertyData["location"], 'postal_code', 'address'),
			"line" : getValue(propertyData["location"], 'line', 'address'),
			"city" : getValue(propertyData["location"], 'city', 'address'),
			"state" : getValue(propertyData["location"], 'state', 'address'),
			"street_view_url" : getValue(propertyData["location"], 'street_view_url'),
			"lat" : getValue(propertyData["location"]["address"], 'lat', 'coordinate'),
			"lon" : getValue(propertyData["location"]["address"], 'lon', 'coordinate'),
			"primary_photo" : getValue(propertyData, 'href', 'primary_photo'),
			"status" : getValue(propertyData, 'status'),
			"photos" : ",".join(map(lambda photo: photo["href"], propertyData["photos"])) if "photos" in propertyData.keys() and propertyData["photos"] is not None else ""
		}
		success = insertIntoTable("properties", insertJson);

		if success == False:
			logging.warning("Duplicate property - " + propertyData["property_id"] + " on " + county["county_name"]);
			print("This proerty is already scrapped.")
			excludeList.append(propertyData["property_id"]);
			#break
		else:
			# time.sleep(.3)
			# address = insertJson["line"] + ", " + insertJson["city"]  + ", " + insertJson["state_code"] + " " + insertJson["postal_code"]
			# try:
			# 	getRealtyMoleData(propertyData["property_id"], address)
			# except Exception as e:
			# 	print('Exception while calling Realty Mole API')
			# 	traceback.print_exc()
			eachPropertyData = {
				"property_id" : propertyData["property_id"],
				"permalink" : getValue(propertyData, 'permalink'),
				"city" : insertJson["city"],
				"line" : insertJson["line"],
				"state_code" : insertJson["state_code"],
				"postal_code" : insertJson["postal_code"]
			}
			results.append(eachPropertyData)

			all_values.scrapValues(eachPropertyData)
	return results

commandLoc = "cd /var/www/html/realtor-scrapper/selenium; /usr/local/bin/python3.6 realtor.py"

if __name__ == "__main__":
	# propertyData = {
	# 	"property_id" : "1827381121",
	# 	"permalink" : "Vac-Ave-R10-Drt-Vic-101st-Ste_Sun-Village_CA_93543_M18273-81121"
	# };
	# getSinglePropertyData(propertyData);
	# sys.exit()
	reRunAgent = False
	reRunOwner = False
	countyNameProvided = False
	totalArguments = len(sys.argv)
	filterCounty = None

	if totalArguments >= 2 and sys.argv[1] == 'reRunAgent':
		reRunAgent = True
		filterCounty = sys.argv[2] if totalArguments == 3 else None
	elif len(sys.argv) >= 2 and sys.argv[1] == 'reRunOwner':
		reRunOwner = True
		filterCounty = sys.argv[2] if totalArguments == 3 else None
	elif len(sys.argv) >= 2 and sys.argv[1] == 'reRun':
		reRunOwner = True
		reRunAgent = True
		filterCounty = sys.argv[2] if totalArguments == 3 else None
	elif len(sys.argv) == 2:
		filterCounty = sys.argv[1]

	countyNameProvided = True if filterCounty is not None else False
	print(reRunAgent)
	print(reRunOwner)
	print(countyNameProvided)
	print(filterCounty)

	reRunOwner = False # Temporary Disabling this script
	counties = getCounties(filterCounty)
	print(counties)
	#sys.exit()
	if reRunAgent == True or reRunOwner == True:
		procs = []
		if len(counties) != 1:
			for eachCounty in counties:
				command = commandLoc + ' ' + sys.argv[1] + " "  + eachCounty['county_name'] + ' 2>/dev/null >/dev/null &'
				print(command)
				os.system(command)
				time.sleep(3)

		else:
			for eachCounty in counties:
				updateTable("counties", "id", str(eachCounty["id"]), {
					'rerun_status' : "running",
					'rerun_started_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				})
				procs = []
				if reRunAgent == True:
					updateTable("counties", "id", str(eachCounty["id"]), {
						'rerun_agent_status' : "running",
						'rerun_agent_started_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					})
					runnableRecordList = getReRunnableAgentRecords(eachCounty['id'])
					for eachProperty in runnableRecordList:
						proc = Process(target=getSinglePropertyData, args=(eachProperty,))
						proc.start()
						procs.append(proc)

						# Run multithreading for configured thread
						if len(procs) == process_thread_count:
							for proc in procs:
								#waiting here to finish all processes
								proc.join()

							print("Resetting procs now")
							procs = []
					for proc in procs:
						proc.join()
					updateTable("counties", "id", str(eachCounty["id"]), {
						'rerun_agent_status' : "finished",
						'rerun_agent_finished_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					})

				procs = []
				if reRunOwner == True:
					updateTable("counties", "id", str(eachCounty["id"]), {
						'rerun_owner_stauts' : "running",
						'rerun_owner_started_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					})
					runnableRecordList = getReRunnableOwnerRecords(eachCounty['id'])
					for eachProperty in runnableRecordList:
						proc = Process(target=getMellisaData, args=(eachProperty,))
						proc.start()
						procs.append(proc)

						# Run multithreading for configured thread
						if len(procs) == process_thread_count:
							for proc in procs:
								#waiting here to finish all processes
								proc.join()

							print("Resetting procs now")
							procs = []

					for proc in procs:
						proc.join()

					updateTable("counties", "id", str(eachCounty["id"]), {
						'rerun_owner_stauts' : "finished",
						'rerun_owner_finished_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
					})
				updateTable("counties", "id", str(eachCounty["id"]), {
					'rerun_status' : "finished",
					'rerun_finished_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				})

	elif countyNameProvided == True or len(counties) == 1:
		# Run the county Data here;
		for eachCounty in counties:
			updateTable("counties", "id", str(eachCounty["id"]), {
				'run_status' : "running",
				'total_records' : 0,
				'started_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			})

			totalPages, results, totalRecords = getTotalRecords(eachCounty)

			updateTable("counties", "id", str(eachCounty["id"]), {
				'total_records' : str(totalRecords),
			})

			print("Total Pages - " + str(totalPages))

			procs = []
			logging.warning("Total Pages - " + str(totalPages));
			for pageNo in range(2, totalPages + 1):
				print("Running Page NO - " + str(pageNo))
				logging.warning("Running Page NO - " + str(pageNo));

				proc = Process(target=getSingleCountyData, args=(eachCounty, results,  1, pageNo,))
				proc.start()
				procs.append(proc)

			for proc in procs:
				proc.join()

			procs = []
			runnableRecordList = getReRunnableAgentRecords(eachCounty['id'])
			for eachProperty in runnableRecordList:
				proc = Process(target=getSinglePropertyData, args=(eachProperty,))
				proc.start()
				procs.append(proc)
				if len(procs) == process_thread_count:
					for proc in procs:
						proc.join()
					procs = []

			runnableRecordList = getReRunnableOwnerRecords(eachCounty['id'])
			for eachProperty in runnableRecordList:
				proc = Process(target=getMellisaData, args=(eachProperty,))
				proc.start()
				procs.append(proc)
				if len(procs) == process_thread_count:
					for proc in procs:
						proc.join()
					procs = []

			for proc in procs:
				proc.join()

			updateTable("counties", "id", str(eachCounty["id"]), {
				'run_status' : "finished",
				'finished_at' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			})

	else:
		for eachCounty in counties:
			#Now invoke each county as a separate command so that we get thread independence.
			command = commandLoc + ' ' + eachCounty['county_name'] + ' 2>/dev/null >/dev/null &'
			print(command)
			os.system(command)
