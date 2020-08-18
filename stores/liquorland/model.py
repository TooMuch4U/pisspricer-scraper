import aiohttp
from custom_exceptions import LiquorlandException
import custom_requests as req


class LiquorlandModel:

    def __init__(self, printer):
        self.print_func = printer

    @staticmethod
    def get_locations():
        """
        Get a json list of liquorland locations
        :return: List of liquorland store locations
        """
        task = "get_locations"
        url = "https://www.liquorland.co.nz/themes/liquorland/scripts/StoreFinder/branches.json?v6"
        res = req.get(url)
        if res.status != 200:
            raise LiquorlandException(res, task)
        locations = res.json()
        return locations

    def get_items(self):
        pass
