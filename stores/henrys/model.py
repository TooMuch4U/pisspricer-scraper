import custom_requests as req
import requests
from stores.henrys.store_processor import process_stores_page


class HenrysModel:

    def __init__(self, printer):
        self.print_func = printer

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

