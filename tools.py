import os
import requests
from custom_exceptions import *
from datetime import datetime


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
