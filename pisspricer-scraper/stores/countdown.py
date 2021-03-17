import api
from stores import generic_store
import time
import requests
import tools
from custom_exceptions import *
import custom_requests as custom_reqs
from pisspricer import Pisspricer


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

        # Async post all new items
        if len(new_items) != 0:
            self.print_progress(0, len(new_items), "upload new items")
            new_items_skus = tools.async_post_items(new_items,
                                                    api.url + "/items",
                                                    headers=api.headers,
                                                    printer=(self.print_progress, len(new_items), "upload new items"))

        # Get a set of barcodes from pisspricer
        barcodes_res = requests.get(api.url + "/barcodes",
                                    headers=api.headers)
        tools.check_pisspricer_res(barcodes_res, task)
        barcodes = barcodes_res.json()

        # Upload images for new items
        pisspricer = Pisspricer(api)
        new_images_url = []

        # Iterate through items and assign image dicts
        for cat_list in cd_items_dict.values():
            for cat_dict in cat_list:
                items = cat_dict['items']
                for item in items:
                    try:
                        image_url = item["images"]["big"]
                        barcode = item["barcode"]
                        sku = barcodes[barcode][0]
                        new_images_url.append({"sku": sku, "image_url": image_url})
                    except Exception as err:
                        tools.log_error(err)

        pisspricer.upload_new_images(new_images_url, self.print_progress)

        new_images = self._get_new_images(new_items, barcodes)
        # if len(new_images) != 0:
        #     self.print_progress(0, len(new_images), "upload item images")
        #     responses = custom_reqs.post_images(new_images,
        #                                         f"{api.url}/items",
        #                                         headers=api.headers,
        #                                         printer=(self.print_progress, len(new_images), "upload item images"))

        # Put price data into pisspricer api
        prices_list = self._create_price_list(stores, cd_items_dict, barcodes)
        price_data_res = custom_reqs.put_prices(prices_list,
                                                api.url,
                                                headers=api.headers)

    @staticmethod
    def _create_price_list(stores, cd_items_dict, barcodes):
        """
        Iterate through countdown items and create price data
        :param stores: List of countdown stores from pisspricer api
        :param cd_items_dict: Dictionary of countdown stores and items
        :param barcodes: Dictionary of barcodes from pisspricer api
        :return: List of (sku, store_id, payload) tuples
        """

        # Create a dict of {"cd_id": "store_id"}
        store_dict = {}
        for store in stores:
            cd_id = store["internalId"]
            store_dict[cd_id] = store["storeId"]

        # Create a list of price data tuples
        price_data = []
        for cd_id, cats in cd_items_dict.items():
            for cat_obj in cats:
                items = cat_obj["items"]
                for item in items:
                    try:

                        # Create payload
                        price_item = {
                            "price": item["price"]["originalPrice"],
                            "internalSku": item["sku"],
                        }
                        if item["price"]["isSpecial"]:
                            price_item["salePrice"] = item["price"]["salePrice"]

                        # Get storeId and sku
                        store_id = store_dict[cd_id]
                        sku = barcodes[item["barcode"]][0]

                        # Add data to list
                        price_data.append((sku, store_id, price_item,))
                    except Exception as err:
                        tools.log_error(err)

        return price_data

    @staticmethod
    def _get_new_images(new_items, barcodes):
        """
        Returns a list of new images
        :param new_items: List of dict items that are new
        :param barcodes: Dictionary of barcodes from pisspricer api
        :return: List of (sku, image)
        """
        new_images_url = []
        for item in new_items:
            barcode = item["barcode"]
            if barcode in barcodes:
                sku = barcodes[barcode][0]
                new_images_url.append((sku, item["image_url"]))
        new_images = custom_reqs.async_get_images(new_images_url)
        return new_images

    @staticmethod
    def _get_new_items(cd_items, barcodes, cur_cats):
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
                                "categoryId": cat_id,
                                "image_url": item["images"]["big"],
                            }
                            if subcat_id is not None:
                                new_item["subcategoryId"] = subcat_id
                            new_items.append(new_item)
                            new_barcodes.add(item["barcode"])
                except Exception as err:
                    tools.log_error(err)
                    # raise err

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

        return items_dict

