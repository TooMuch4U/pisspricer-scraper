from pisspricer import Pisspricer
import tools
import re
import categories as cat
from bs4 import BeautifulSoup
import json


def process_henry_items(items):
    """
    Processes a list of items from henrys api, converts into pisspricer relevant info
    :param items: List of items from henrys api
    :return: List of items for pisspricer api
        [
            {
              "name": "string",
              "brand": "string",
              "categoryId": 0,
              "subcategoryId": 0,
              "stdDrinks": 0,
              "alcoholContent": 0,
              "volumeEach": 0,
              "barcode": "string",
              "salePrice": 0,
              "price": 0,
              "stock": "string",
              "internalSku": "string",
              "url": "string"
            }
        ]
    """
    new_items = []

    # Get most item details
    for henry_item in items:
        try:
            new_item = process_henry_item(henry_item)
            new_items.append(new_item)
        except Exception as err:
            tools.log_error(err)

    print(items[0])
    return new_items


def process_henry_item(item):
    """
    Processes on henrys item
    :param item: Dict from henrys api
    :return: Dict with item info for pisspricer api, excluding barcodes
    """
    new_item = dict()
    new_item['name'] = item['title']
    new_item['brand'] = None
    if item['isOnSpecial'] and item.get('savings', None) is not None:
        new_item['salePrice'] = round(item['productPrice'], 2)
        new_item['price'] = new_item['salePrice'] + item['savings']
    else:
        new_item['price'] = round(item['productPrice'], 2)
        new_item['salePrice'] = None
    new_item['volumeEach'] = get_volume(new_item['name'])
    new_item['internalSku'] = str(item['id'])
    new_item['url'] = item['url']
    new_item['henryStores'] = item['sites']
    # new_item['henryCat'] = item['department']
    new_item['categoryId'], new_item['subcategoryId'] = get_category_info(item['subDepartmentKey'])

    return new_item


def get_volume(name):
    """
    Infers the volume from the items name
    :param name: Name of the item
    :return: The volume of the item, or None if it can't be found
    """
    name = name.lower()
    m = re.search(r"([0-9]+.)?[0-9]+(ml|l)", name)
    if m is not None:
        vol_str = name[m.start():m.end()]
        vol = ""
        for i, char in enumerate(vol_str):
            if char in set('. 0 1 2 3 4 5 6 7 8 9'.split(' ')):
                vol += char
            else:
                if char == 'm':
                    return float(vol)
                else:
                    return float(vol) * 1000
        return None
    return None


def process_item_pages(responses):
    """
    Extracts barcodes and image urls from pages
    :param responses: List of (item, response) 2-tuples
    :return: List of dict item objects
    """
    items = []
    for item, res in responses:
        try:
            new_item = process_item_page(item, res)
            items.append(new_item)
        except Exception as err:
            tools.log_error(err)
    return items

def process_item_page(item, response):
    """
    Adds barcode and image_url to item
    :param item: Item dict
    :param response: Response object for the page
    :return: item
    """
    res_soup = BeautifulSoup(response.text(), features="html.parser")

    # Finding barcode
    scripts = res_soup.findAll('script')
    item['barcode'] = None
    for script in scripts:
        try:
            if 'sku' in script.string:
                item_info = script.string
                item['barcode'] = json.loads(item_info)['@graph'][0]['sku']
                break
        except Exception:
            pass

    # Image url
    item['image_url'] = res_soup.find("img", {"class": "w-full"}).get('src')

    return item


def get_category_info(dept_key):
    """
    Gets the category id for the item
    :return: 2-tuple of (category_id, subcategory_id)
    """
    beer_keys = {
        24350, 13587, 24680, 24675, 24676, 24677, 24349,
        24351, 24352, 24350, 24351, 24352, 24680, 24675,
        24676, 24677, 24349, 24589, 24673, 24674, 24679
    }
    cider_keys = {13587}
    wine_keys = {
        13651, 13650, 13652, 13652, 13651, 13650, 13653,
        13654, 13655, 13656, 13579, 13658, 13659, 13660,
        13661, 13662, 13664, 13583, 13657, 13667, 13580,
        13663, 13670, 13672, 13577
    }
    spirits = {
        23625, 23626, 23627, 23628, 23634, 23630, 23633,
        23635
    }
    liqueurs = {23629}
    rtd = {
        16639, 16642, 16643, 16644, 16648, 16649
    }

    # Check which category the dept key is
    if dept_key in beer_keys:
        return cat.beer, None
    elif dept_key in cider_keys:
        return cat.cider, None
    elif dept_key in wine_keys:
        return cat.wine, None
    elif dept_key in spirits:
        return cat.spirits, None
    elif dept_key in liqueurs:
        return cat.liqueurs, None
    elif dept_key in rtd:
        return cat.rtd, None

    return None, None

