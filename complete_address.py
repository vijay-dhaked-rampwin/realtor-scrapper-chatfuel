import requests

GOOGLE_API_KEY="AIzaSyDwe2yPwkbcCRJw4PCSD_WatqmUuLHRbDs"
def extract_full_address(address_or_zipcode):
    add = ""
    api_key = GOOGLE_API_KEY
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    endpoint = f"{base_url}?address={address_or_zipcode}&key={api_key}"
    r = requests.get(endpoint)
    if r.status_code not in range(200, 299):
        return None, None
    try:
        '''
        This try block incase any of our inputs are invalid. This is done instead
        of actually writing out handlers for all kinds of responses.
        '''
        #print(r.text)
        results = r.json()['results'][0]
        #lat = results['geometry']['location']['lat']
        #lng = results['geometry']['location']['lng']
        add=results["formatted_address"]
    except:
        pass
    return add
