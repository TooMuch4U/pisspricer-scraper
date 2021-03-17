from pisspricer import Pisspricer
from stores.generic_store import Store
from stores.liquorland import model as liquorland_model
import api


class Liquorland(Store):

    brand_id = 6

    def __init__(self):
        self.model = liquorland_model.LiquorlandModel(printer=self.print_progress)
        super().__init__()

    def update_locations(self):
        """
        Find store locations and add them to pisspricer if new
        :return: None
        """
        # Get locations
        locations = self.model.get_locations()
        stores = []
        for location in locations:
            # Only take stores in range
            if 99 < location['ID'] < 999:

                # Create address string
                address_items = [
                    location['Address2'],
                    location['City'],
                    location['State'],
                    location['PostCode']
                ]
                address = location['Address1']
                for item in address_items:
                    if item is not None and item != "":
                        address += f", {item}"
                address += ", New Zealand"

                # Create Store Dict
                store = {
                    "name": location["Name"],
                    "url": "https://www.shop.liquorland.co.nz",
                    "address": address,
                    "postcode": location['PostCode'],
                    "internalId": str(location['ID']),
                    "region": None,
                    "region_lat": None,
                    "region_lng": None,
                    "lattitude": None,
                    "longitude": None
                }

                # Add store to store list
                stores.append(store)

        # Post Stores
        pisspricer_con = Pisspricer(api)
        pisspricer_con.upload_new_stores(stores,
                                         self.brand_id,
                                         printer=(self.print_progress, len(stores), "update locations"))

    def update_all_items(self):

        pisspricer = Pisspricer(api)

        # Get stores from pisspricer
        stores = pisspricer.get_stores(self.brand_id)

        # Get items from liquorland model
        items = self.model.get_items(stores)

        # Create new products with pisspricer api
        pisspricer.update_item_prices(items, self.brand_id, "liquorland", self.print_progress)



