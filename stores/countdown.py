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
    page_lim = 120
    page_lim_str = "&size=" + str(page_lim)

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

        # Post stores to pisspricer api
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
        """ Updates all items for all known Countdown store """
        task = "update_all_items"

        # Get all current countdown stores
        stores_res = requests.get(api.url + "/stores",
                                  headers=api.headers,
                                  params={"brandId": Countdown.cd_brand_id})
        if not stores_res.ok:
            raise PisspricerApiException(stores_res, task)
        stores = stores_res.json()

        # Get a set of barcodes from pisspricer
        barcodes_res = requests.get(api.url + "/barcodes",
                                    headers=api.headers)
        tools.check_pisspricer_res(barcodes_res, task)
        barcodes = barcodes_res.json()

        # Iterate through stores and get items from countdown api
        cd_items_dict = self._get_cd_items(stores)

        # Get categories
        categories_res = requests.get(api.url + "/categories", headers=api.headers)
        tools.check_pisspricer_res(categories_res, task)
        categories = categories_res.json()

        # Get a list of new items
        new_items = self._get_new_items(cd_items_dict, barcodes, categories)
        print(f"Items length: {len(new_items)}")

        # Async post all new items
        new_items_list = tools.async_post_list(new_items,
                                                   api.url + "/items",
                                                   api.headers)
        # TODO Implement inserting price data

    def _get_new_items(self, cd_items, barcodes, cur_cats):
        """
        Take a dictionary of countdown items and return a list of items that aren't in the database.
        Categorys that aren't in database get added as it goes
        :param cd_items: Dictionary of countdown items
        :param barcodes: Dictionary of barcodes that are currently in the database
        :return: List of json items that aren't in the database
        """
        new_items = []
        new_barcodes = set()
        for store_id, cats in cd_items.items():
            for cat_obj in cats:
                try:
                    # Get cats
                    cat = cat_obj["cat"].lower()
                    subcat = None if cat_obj["subcat"] is None else cat_obj["subcat"].lower()

                    # Create cat and subcat if they dont exist
                    if cat not in cur_cats:
                        # create cat
                        cat_id = tools.post_category(cat)
                        # Add to dict
                        cur_cats[cat] = {
                            "category": cat,
                            "categoryId": cat_id,
                            "subcategories": []
                        }
                    else:
                        cat_id = cur_cats[cat]["categoryId"]

                    subcat_id = None
                    if subcat is not None:
                        # Subcat specified
                        subcats = cur_cats[cat]["subcategories"]
                        for sub in subcats:
                            if sub["subcategory"] == subcat:
                                subcat_id = sub["subcategoryId"]
                                break

                        if subcat_id is None:
                            # Subcat needs to be created
                            subcat_id = tools.post_subcategory(cat_id, subcat)
                            cur_cats[cat]["subcategories"].append({
                                "subcategory": subcat,
                                "subcategoryId": subcat_id
                            })

                    items = cat_obj["items"]
                    for item in items:
                        if item["barcode"] not in barcodes and item["barcode"] not in new_barcodes:
                            volume = item["size"]["volumeSize"]
                            new_item = {
                                "name": item["name"] + (" " + volume if volume is not None else ""),
                                "brand": item["brand"],
                                "barcode": item["barcode"],
                                "categoryId": cat_id
                            }
                            if subcat_id is not None:
                                new_item["subcategoryId"] = subcat_id
                            new_items.append(new_item)
                            new_barcodes.add(item["barcode"])
                except Exception as err:
                    raise err
                    tools.log_error(err)

        return new_items

    def _get_cd_items(self, stores):
        """
        Gets all items from Countdown API

        :param stores: List of Countdown stores from pisspricer api
        :return: Dictionary of items {cd_id: [{'cat': str, 'subcat': str, 'items': []}] }
        """
        task = "_get_cd_items"
        item_url = self.cd_base_url + self.cd_items + self.page_lim_str

        items_dict = dict()
        count = 0
        self.print_progress(0, len(stores), task)
        for store in stores:
            try:
                # Set store and get first page items
                self._set_store(store["internalId"])
                items_res = requests.get(item_url,
                                         headers=self.cd_headers,
                                         cookies=self.cookies)
                if not items_res.ok:
                    raise CountdownApiException(items_res, task)
                items_json = items_res.json()

                # Generate url's
                cats = items_json["dasFacets"]
                urls = []
                for cat in cats:
                    cat_name = cat["name"]
                    cat_count = cat["productCount"]
                    url_end = f"&dasFilter=Aisle;;{cat_name.replace(' ', '-').replace('&', '')};false"
                    if "wine" in cat_name:
                        cat_info = {
                            "cat": "Wine",
                            "subcat": cat_name
                        }
                    else:
                        cat_info = {
                            "cat": cat_name,
                            "subcat": None
                        }
                    urls += tools.generate_url_pages(item_url + "&page=", cat_count, self.page_lim,
                                                     url_end=url_end, carry=cat_info)
                responses = tools.async_get_list(urls, headers=self.cd_headers, cookies=self.cookies)

                # Iterate through responses and make a list of data
                items = []
                for res in responses:
                    # Check if cat is already in list
                    res_cat = res["carry"]
                    cat_in_list = False
                    index = -1
                    for i, cat in enumerate(items):
                        if cat["cat"] == res_cat["cat"] and cat["subcat"] == res_cat["subcat"]:
                            cat_in_list = True
                            index = i
                            break

                    if cat_in_list:
                        items[i]["items"] += res['products']['items']
                    else:
                        items.append({"cat": res_cat["cat"],
                                      "subcat": res_cat["subcat"],
                                      "items": res['products']['items']})

                # Assign items to dict
                items_dict[store["internalId"]] = items

            except Exception as err:
                tools.log_error(err)
            finally:
                count += 1
                self.print_progress(count, len(stores), task)
            break # TODO Remove to do all stores

        return items_dict

