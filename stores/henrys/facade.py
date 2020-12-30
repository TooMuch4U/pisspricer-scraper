from stores.generic_store import Store
from stores.henrys.model import HenrysModel
from pisspricer import Pisspricer
import api


class Henrys(Store):

    BRAND_ID = 7

    def __init__(self):
        super().__init__()
        self.model = HenrysModel(self.print_progress, self.BRAND_ID)

    def update_locations(self):
        """
        Gets locations from henrys website and upload new stores
        :return: None
        """
        # Get list of locations
        locations = self.model.get_locations()

        # Upload new locations
        pisspricer = Pisspricer(api)
        pisspricer.upload_new_stores(locations, self.BRAND_ID,
                                     (self.print_progress, len(locations), 'Get Locations'))

    def update_all_items(self):
        items = self.model.get_items()
        pisspricer = Pisspricer(api)
        pisspricer.update_item_prices(items, self.BRAND_ID, 'Henrys', self.print_progress)
        # TODO Run and check if works

if __name__ == '__main__':
    henrys = Henrys()
    henrys.update_all_items()
