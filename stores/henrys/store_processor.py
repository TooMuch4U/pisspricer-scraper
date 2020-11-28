from bs4 import BeautifulSoup
import json
import tools


def process_stores_page(page_html):
    """
    Processes henrys stores page into list of dictionary store items
    :param page_html: String of page html
    :return: List of store dictionary items
        {
            name: "required|string",
            url: "required|string",
            region: "required|string",
            region_lat: "numeric",
            region_lng: "numeric",
            address: "required|string",
            postcode: "numeric",
            lattitude: "numeric",
            longitude: "numeric"
            internalId: "string"
        }
    """
    # Parse the html
    soup = BeautifulSoup(page_html, features="html.parser")

    # Get the store info json
    store_json_list = json.loads(soup.find('store-locations')[':locations'])
    stores = []
    for store_json in store_json_list:
        try:
            store = process_store_json(store_json)
            stores.append(store)
        except Exception as err:
            tools.log_error(err)
    return stores


def process_store_json(store_json):
    """
    Processes a store div and returns a dictionary of the stores info
    :param store_json: Store dict object
    :return: Dictionary object with stores info
        {
            name: "required|string",
            url: "required|string",
            region: "required|string",
            region_lat: "numeric",
            region_lng: "numeric",
            address: "required|string",
            postcode: "numeric",
            lattitude: "numeric",
            longitude: "numeric"
            internalId: "string"
        }
    """
    store = dict()

    store['name'] = store_json['title']
    store['url'] = f"https://www.henrys.co.nz/{store_json['uri']}"
    store['region'] = store_json['regions']
    store['region_lat'] = None
    store['region_lng'] = None
    store['address'] = store_json['locationAddress'][:-4].replace('\n', ', ')
    store['postcode'] = int(store_json['locationAddress'][-4:])
    store['lattitude'] = float(store_json['locationCoordinates'][0]['latitude'])
    store['longitude'] = float(store_json['locationCoordinates'][0]['longitude'])
    store['internalId'] = str(store_json['siteID'])

    return store

