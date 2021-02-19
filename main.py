from flask import Flask, redirect,render_template, stream_with_context, request, Response , jsonify
from threading import Thread
import zillow_valuation
import redfin_valuation
import xome_valuation
import eppraisal_valuation
import remax_valuation
import chase_valuation
import forsalebyowner_valuation
import mellisa_valuation
import realtor_valuation
import requests
import time
from complete_address import extract_full_address
from python_chatfuel_class import  Chatfuel

#from Config import Config
from scraphelper import Send_estimation_request_data_Data,AddToestimation_requests,UpdateToestimation_requests,AddToestimation_request_data
app = Flask(__name__)

@app.route("/getCompleteAddress")
def call_google_api():
    raw_address = request.args.get('raw_address')
    full_address=extract_full_address(raw_address)
    print(full_address)
    if not full_address:
        full_address="19 T"
    return jsonify({
      "set_attributes":
        {
          "full_address": full_address
        }
    })

@app.route("/sendPrice")
def send_price():
    req_id= request.args.get('req_id')
    all_prices=Send_estimation_request_data_Data(req_id)
    title="Estimated Price On "
    all_image_url=[
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/zillow.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/redfin.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/xome.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/remax.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/eppraisal.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/chase.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/forsalebyowner.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/mellisa.png",
        "https://realtorscrapping.s3.ap-south-1.amazonaws.com/realtor.png"
    ]
    data_not_found=[]
    for i in range(9):
        if not all_prices[i][1]:
            data_not_found.append(i)

    all_elements=[]
    for i in range(9):
        if i not in data_not_found:
            d={}
            d['title']=title+all_prices[i][0]
            d['image_url']=all_image_url[i]
            d['subtitle']=all_prices[i][1]
            d['buttons']=[
                {
                  "type":"web_url",
                  "url":all_prices[i][2],
                  "title":"View on site"
                }
            ]
            all_elements.append(d)
    #print(all_elements)
    return {
 "messages": [
    {
      "attachment":{
        "type":"template",
        "payload":{
          "template_type":"generic",
          "image_aspect_ratio": "square",
          "elements":all_elements
        }
      }
    }
  ]
}


def runScrapper(raw_address,req_id):
    #this function is responsible for gatherring data, storing data, and send any further communication
    all_prices={}
    thread_list=[]
    all_scrapper_name=['zillow','redfin','xome','remax','eppraisal','chase','forsalebyowner','mellisa','realtor']
    for scrapper in all_scrapper_name:
        all_prices[scrapper]=dict()

    thread = Thread(target=zillow_valuation.search_price_for_address, args=(raw_address,all_prices['zillow']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=redfin_valuation.search_price_for_address, args=(raw_address,all_prices['redfin']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=xome_valuation.getXomeSingleProperty, args=(raw_address,all_prices['xome']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=remax_valuation.search_price_for_address, args=(raw_address,all_prices['remax']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=eppraisal_valuation.search_price_for_address, args=(raw_address,all_prices['eppraisal']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=chase_valuation.search_price_for_address, args=(raw_address,all_prices['chase']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=forsalebyowner_valuation.search_price_for_address, args=(raw_address,all_prices['forsalebyowner']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=mellisa_valuation.getMellisaData, args=(raw_address,all_prices['mellisa']))
    thread.start()
    thread_list.append(thread)

    thread = Thread(target=realtor_valuation.search_price_for_address, args=(raw_address,all_prices['realtor']))
    thread.start()
    thread_list.append(thread)


    for thread in thread_list:
        thread.join()

    print("All threads are completed")

    for scrapper in all_scrapper_name:
        AddToestimation_request_data(all_prices[scrapper][scrapper+"_url"],req_id,scrapper,all_prices[scrapper][scrapper+"_price"])

    user_id=UpdateToestimation_requests(req_id)
    user_id=user_id[0][0]
    broadcasting_api=f"https://api.chatfuel.com/bots/601bfa40676eff4aa52ec86c/users/{user_id}/send?chatfuel_token=9ILa78W3A4u4pJye3UVdXGQCQryPykKaNZ7zaNiobLWJvmiUaVRsFQBH9wEzt4hA&chatfuel_block_id=601ceaa4676eff4aa51e7619"
    payload={}
    headers = {'Cookie': 'INGRESS_INT_ROUTE=1612519705.026.53.876466'}
    response = requests.request("POST", broadcasting_api, headers=headers, data=payload)
    print(user_id)
    #print("URLLLL:" ,broadcasting_api)
    #print(response)

    # send the information to WA/fb/telegram


@app.route("/placeRequest")
def get_bot_response():
    full_address = request.args.get('full_address')
    raw_address = request.args.get('raw_address')
    user_id= request.args.get('user_id')
    source= request.args.get('source')
    req_id=AddToestimation_requests(raw_address,full_address,1,user_id,source)

    print("request id is the : ",req_id)
    thread = Thread(target=runScrapper, args=(full_address,req_id))
    thread.start()

    return jsonify({
      "set_attributes":
        {
          "request_id": req_id
        }
    })

if __name__ == "__main__":
    app.run()
