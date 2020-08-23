import os
import requests
from custom_exceptions import *
from datetime import datetime
import math
import api
from custom_requests import async_get_list, async_post_items


# Print iterations progress
def print_progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def geocode_address(address):
    """ Geocodes an address into lattitude longitude coordinates """
    key = os.getenv("maps_api_key")
    res = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={key}")
    if not res.ok:
        raise GoogleApiException(res, f"Geocoding address '{address}'")
    else:
        data = res.json()
        if data["status"] != "OK":
            raise GoogleApiException(res, f"Geocoding address '{address}', return data '{data}'")
        else:
            lat = data["results"][0]["geometry"]["location"]["lat"]
            lng = data["results"][0]["geometry"]["location"]["lng"]
            address = data["results"][0]["formatted_address"]
            postcode = ""
            region = ""
            for comp in data["results"][0]["address_components"]:
                if "postal_code" in comp["types"]:
                    postcode = comp["short_name"]
                if "administrative_area_level_1" in comp["types"]:
                    region = comp["long_name"]
            return lat, lng, address, postcode, region


def log_error(error):
    """ To be implemented """
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    file_name = "log.txt"
    f = open(file_name, "a")
    f.write(f"{dt_string}: {str(error)}\n")
    f.close()


def generate_url_pages(url1, total, per_page, start_page=1, offset=0, url_end="", carry=None):
    """
    Generate urls for multi-page requests

    :param url1: First half of URL (before page no)
    :param url_end: Second half of URL (after page no)
    :param total: Total number of items
    :param per_page: Number of items per page
    :param start_page: Page number to start from. 1 indexing
    :param offset: Offset page numbers (-1 for 0 indexing pages)
    :param carry: Data that can be carried to every url
    :return: List of generated urls
    """
    urls = []
    pages = math.ceil(total / per_page)
    for p in range(start_page, pages+1):
        url = f"{url1}{p + offset}{url_end}"
        urls.append({"url": url, "carry": carry})
    return urls


def check_pisspricer_res(res, task):
    """
    Checks pisspricer api response object. Throws error if not ok
    :param res: Response object
    :param task: Task string for exception
    :return: None
    """
    if not res.ok:
        raise PisspricerApiException(res, task)


def get_cat_id(categories, cat, subcat):
    """
    Returns the categoryId and subcat Id if they exists
    :param categories: Categories from pisspricer api
    :param cat: Cat name to look for
    :param subcat: Subcat name to look for
    :return: catId, subcatId
    """
    cat_id = None
    subcat_id = None
    if cat in categories:
        cat_id = categories[cat]["categoryId"]
        for sub in categories[cat]["categoryId"]["subcategories"]:
            if sub["subcategory"] == subcat:
                subcat_id = sub["subcategoryId"]
                break

    return cat_id, subcat_id


def post_category(cat):
    """
    Posts a new category to pisspricer api
    :param cat: String for new category name
    :return: Category ID
    """
    payload = {"category": cat}
    res = requests.post(api.url + "/categories", json=payload, headers=api.headers)
    if not res.ok:
        raise PisspricerApiException(res, f"Posting category '{cat}'")
    return res.json()["categoryId"]


def post_subcategory(cat_id, subcat):
    """
    Post a subcategory to pisspricer api
    :param cat_id: Parent category id
    :param subcat: String for new subcat
    :return: subcat_id
    """
    payload = {"subcategory": subcat}
    res = requests.post(api.url + f"/categories/{cat_id}/subcategories",
                        headers=api.headers,
                        json=payload)
    if not res.ok:
        raise PisspricerApiException(res, f"Posting subcategory '{subcat}', for category with id {cat_id}")

    return res.json()["subcategoryId"]


def get_barcode(barcode_string):
    """
    Finds where a barcode ends in a string and returns it
    :param barcode_string:
    :return: Barcode string or None
    """
    barcode = ""
    for i, char in enumerate(barcode_string):
        if not char.isnumeric():
            break
        barcode += char

    if i < 11:
        barcode = None

    return barcode



