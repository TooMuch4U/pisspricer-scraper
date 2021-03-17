import custom_requests as req
import requests
from stores.henrys.store_processor import process_stores_page
import asyncio
from pisspricer import Pisspricer
import api
from stores.generic_model import Model
from stores.henrys.item_processor import process_henry_items, process_item_pages
import copy


class HenrysModel(Model):

    def __init__(self, printer, brand_id):
        self.print_func = printer
        self.BRAND_ID = brand_id

    @staticmethod
    def get_locations():
        """
        Gets locations from
        :return:
        """
        url = "https://www.henrys.co.nz/store-locations"
        res = requests.get(url)
        stores = process_stores_page(res.content)
        return stores

    def get_items(self):
        """
        Gets all items from the henrys website
        :return: List of store items
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
        henry_api_items = self._get_henry_items()
        items_no_barcode = process_henry_items(henry_api_items)
        print(len(items_no_barcode))
        items = self.get_items_barcodes(items_no_barcode)
        return items

    def get_items_barcodes(self, items):
        """
        Gets barcodes and image urls for all items
        :param items: List of items
        :return: List of dict items with barcode, and image_url added
        """
        request_list = [(item['url'], item) for item in items]
        iteration = [0]
        self.print_func(0, len(request_list), 'Get Item barcodes')
        responses = asyncio.run(
            req.create_async_tasks(
                request_list,
                {
                    "printer": (
                        self.print_func,
                        len(request_list),
                        'Get item barcodes'
                    ),
                    "iteration": iteration
                },
                self._async_get))

        items = process_item_pages(responses)
        new_items = self.add_store_ids(items)
        return new_items

    def add_store_ids(self, items):
        """ Returns a new item list based on the henry stores """
        cur_locations_res = req.get(api.url + "/stores",
                                    headers=api.headers,
                                    params={"brandId": self.BRAND_ID})
        cur_locs = cur_locations_res.json()
        store_id_mappings = {int(loc['internalId']): loc['storeId'] for loc in cur_locs}
        new_items = []
        for item in items:
            for internal_store_id in item['henryStores']:
                new_item = copy.deepcopy(item)
                del new_item['henryStores']
                if int(internal_store_id) in store_id_mappings:
                    new_item['storeId'] = store_id_mappings[int(internal_store_id)]
                    new_items.append(new_item)

        return new_items

    def _get_henry_items(self):
        """
        Gets a list of items from henrys website. Excluding barcodes
        :return: List of items from henrys api
        """
        category_ids = [16639,16642,16643,16644,16648,16649,23625,23626,23627,23628,23634,23630,23633,23635,23629,
                       13651,13650,13652,13652,13651,13650,13653,13654,13655,13656,13579,13658,13659,13660,13661,
                       13662,13664,13583,13657,13667,13580,13663,13670,13672,13577,24350,13587,24680,24675,24676,
                       24677,24349,24351,24352,24350,24351,24352,13587,24680,24675,24676,24677,24349,24589,24673,
                       24674,24679]
        category_ids_str = [str(cat) for cat in category_ids]
        url = f"https://www.henrys.co.nz/api/products?categories={','.join(category_ids_str)}"

        # Get first page
        first_page = requests.get(url + "&page=0").json()
        total_pages = int(first_page['totalPages'])
        other_pages_urls = [(url + f"&page={i}", None) for i in range(1, total_pages + 1)]

        # Get rest of pages
        iteration = [0]
        self.print_func(0, len(other_pages_urls) - 1, 'Get Items')
        responses = asyncio.run(
            req.create_async_tasks(
                other_pages_urls,
                {
                    "printer": (
                        self.print_func,
                        total_pages - 1,
                        'Get Items'
                    ),
                    "iteration": iteration
                },
                self._async_get))

        # Collate all items in a list
        items = first_page['products']
        for _, page in responses:
            items += page.json()['products']
        return items


