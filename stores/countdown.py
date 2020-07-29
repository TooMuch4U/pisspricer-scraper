import api
from stores import generic_store
import time
import requests
import tools
from custom_exceptions import *


class Countdown(generic_store.Store):

    cd_brand_id = 5
    cd_base_url = "https://shop.countdown.co.nz/api/v1"
    cd_items = "/products?dasFilter=Department%3B%3Bbeer-wine%3Bfalse&target=browse"
    cd_stores = "/addresses/pickup-addresses"
    cd_headers = {"x-requested-with": "OnlineShopping.WebApp"}
    store_url = "https://shop.countdown.co.nz"
    name = "Countdown"

    def __init__(self):
        self.cookies = self.get_session_cookie()
        super().__init__()

    @staticmethod
    def get_session_cookie():
        """ Gets and returns a session cookie from countdown API

            @return cookie  - Dict of cookie containing a Countdown API session id
        """
        res = requests.get(Countdown.cd_base_url + Countdown.cd_items,
                           headers=Countdown.cd_headers)
        return {"ASP.NET_SessionId": res.cookies["ASP.NET_SessionId"]}

    @staticmethod
    def _get_new_stores(cd_json, cur_locations_json):
        """ Returns countdown stores which aren't already in the database

            @param cd_json             - List of stores from Countdown API
            @param cur_locations_json  - List of stores from pisspricer API
            @returns post_list         - List of new stores from Countdown API
        """
        post_list = []
        for location in cd_json["storeAreas"][0]["storeAddresses"]:
            # Check if store location is already in db
            new_location = True
            for cur_location in cur_locations_json:
                if str(cur_location["internalId"]) == str(location["id"]):
                    new_location = False
                    break

            if new_location:
                post_list.append(location)
        return post_list

    @staticmethod
    def _post_stores(post_list, regions):
        """ Iterate through store locations and post to api

            @param post_list    - List of stores from Countdown API to be posted to pisspricer api
            @param regions      - List of regions from pisspricer API
        """

        Countdown.print_progress(0, len(post_list), title=Countdown.name + " Inserting Stores")
        i = 0
        for store_loc in post_list:
            try:
                # Get lat and lng
                address_string = store_loc["name"] + ", " + store_loc["address"] + ", New Zealand"
                lat, lng, address, postcode, region = tools.geocode_address(address_string)

                # Set regionId
                region_id = None
                for reg in regions:
                    if reg["name"] == region:
                        region_id = reg["regionId"]
                if region_id is None:
                    new_region_res = requests.post(api.url + "/regions",
                                                   headers=api.headers,
                                                   json={"name": region})
                    if not new_region_res.ok:
                        raise PisspricerApiException(new_region_res, f"posting to /regions {region}")
                    region_id = new_region_res.json()["regionId"]

                # Set store values
                store = {
                    "name": store_loc["name"],
                    "url": Countdown.store_url,
                    "brandId": Countdown.cd_brand_id,
                    "lattitude": lat,
                    "longitude": lng,
                    "regionId": region_id,
                    "address": address,
                    "postcode": postcode,
                    "internalId": str(store_loc["id"])
                }

                # Post new store
                new_store_res = requests.post(api.url + '/stores',
                                              headers=api.headers,
                                              json=store)
                if not new_store_res.ok:
                    raise PisspricerApiException(new_store_res, f"posting to /stores {store}")

            except ApiException as err:
                tools.log_error(err)

            finally:
                i += 1
                Countdown.print_progress(i, len(post_list))
                if i > 1000:
                    break

    def update_locations(self, debug=False):
        """ Get stores from Countdown API and add all stores which are new """
        task = "update_locations"

        # Get current locations from pisspricer api
        cur_locations_res = requests.get(api.url + "/stores",
                                         headers=api.headers,
                                         params={"brandId": Countdown.cd_brand_id})
        if not cur_locations_res.ok:
            raise PisspricerApiException(cur_locations_res.status_code, task)

        # Get locations from Countdown api
        cd_locations_res = requests.get(Countdown.cd_base_url + Countdown.cd_stores,
                                        headers=Countdown.cd_headers)
        if not cd_locations_res.ok:
            raise CountdownApiException(cd_locations_res.status_code, task)

        # Get regions from pisspricer api
        regions_res = requests.get(api.url + "/regions",
                                   headers=api.headers)
        if not regions_res.ok:
            raise PisspricerApiException(cur_locations_res.status_code, task)

        # Iterate through store locations and check which ones are new
        post_list = self._get_new_stores(cd_locations_res.json(), cur_locations_res.json())

        # Post store to pisspricer api
        self._post_stores(post_list, regions_res.json())

    def _set_store(self, internal_id):
        """ Sets the current store of the session id

            @param internal_id  - The internal id of the store to be used
        """
        task = "_set_store"
        body = {"addressId": int(internal_id)}
        res = requests.put(Countdown.cd_base_url + "/fulfilment/my/pickup-addresses",
                           headers=self.cd_headers,
                           cookies=self.cookies,
                           json=body)
        if not res.ok:
            raise CountdownApiException(res, task)

    def update_all_items(self, debug=False):
        res = requests.get(Countdown.cd_base_url + Countdown.cd_items,
                           headers=Countdown.cd_headers)
        print(res.json())
        time.sleep(10)
        # A List of Items
        items = list(range(0, 57))
        l = len(items)

        # Initial call to print 0% progress
        super().print_progress(0, l)
        for i, item in enumerate(items):
            # Do stuff...
            time.sleep(0.1)
            # Update Progress Bar
            super().print_progress(i + 1, l)


