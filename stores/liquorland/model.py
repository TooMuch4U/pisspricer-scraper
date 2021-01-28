import math

import aiohttp
from bs4 import BeautifulSoup
import asyncio
from custom_exceptions import LiquorlandException
import custom_requests as req
import copy
import tools


class LiquorlandModel:

    cookie = {"viewdesktop": "true",
              "sessiondob": "01/01/1900",
              "VisitorIsAdult": True}
    page_count = 48
    params = {"ps": page_count}
    base_url = "https://www.shop.liquorland.co.nz"
    categories = [
        {"cat": "spirits",
         "id": 9,
         "subcats": [
             ("bourbon", "/Bourbon.aspx", 14),
             ("brandy", "/brandy.aspx", 13),
             ("whisky", "/whisky.aspx", 12),
             ("vodka", "/vodka.aspx", 11),
             ("gin", "/gin.aspx", 10),
             ("rum", "/rum.aspx", 9),
             ("tequila", "/tequila.aspx", 8),
             (None, "/otherspirits.aspx", None)
         ]},
        {"cat": "liqueurs",
         "id": 10,
         "subcats": [
             (None, "/liqueurs.aspx", None)
         ]},
        {"cat": "beer",
         "id": 5,
         "subcats": [
             (None, "/beer.aspx", None),
             (None, "/craftbeer.aspx", None)
         ]},
        {"cat": "wine",
         "id": 7,
         "subcats": [
             ("red", "/redwine.aspx", 6),
             ("white", "/whitewine.aspx", 5),
             ("rose", "/rose.aspx", 7),
             ("sparkling & dessert wine", "/sparklingwine.aspx", 4),
             ("sparkling & dessert wine", "/champagne.aspx", 4),
             ("sparkling & dessert wine", "/port.aspx", 4),
             (None, "/caskwine.aspx", None)
         ]},
        {"cat": "cider",
         "id": 6,
         "subcats": [
             (None, "/cider.aspx", None)
         ]},
        {"cat": "rtd",
         "id": 11,
         "subcats": [
             (None, "/rtds.aspx", None)
         ]}
    ]

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
        new_locations = []
        for location in locations:
            if location["BranchType"] is not None:
                new_locations.append(location)
        return new_locations

    def get_items(self, stores, should_print=True):

        task = "get items from liquorland"
        # Iterate through stores and categories and make items for HTTP get
        first_page_items = []
        for store in stores:
            internal_id = store["internalId"]
            for cat in self.categories:
                for _, endpoint, subcatId in cat["subcats"]:

                    cookies = copy.deepcopy(self.cookie)
                    cookies["selectedStore"] = internal_id

                    item = [
                        f"{self.base_url}{endpoint}",
                        {
                            "categoryId": cat["id"],
                            "subcategoryId": subcatId,
                            "storeId": store["storeId"],
                            "internalId": store["internalId"],
                            "url": f"{self.base_url}{endpoint}",
                        },
                        cookies,
                        self.params
                    ]

                    first_page_items.append(item)

        # Batch get first pages
        iteration = [0]
        responses = asyncio.run(req.create_async_tasks(first_page_items,
                                                       {"printer": (self.print_func,
                                                                    len(first_page_items)-1,
                                                                    task + " 1",
                                                                    iteration)},
                                                       self._async_get_item_page))

        items = []
        requests = []

        if should_print:
            self.print_func(0, len(responses), "process responses liquorland 1")

        for i, (item, res) in enumerate(responses):
            soup = BeautifulSoup(res.text(), features="html.parser")
            item_divs = soup.find_all("div", {"class": "productItemDisplay"})
            for item_div in item_divs:

                # Create a new item
                new_item = self._create_item(item_div, item)
                items.append(new_item)

            # work out anymore requests that need to be made for subsequent pages, if any
            item_count = self._get_page_item_count(soup)
            n_pages = math.ceil(item_count / self.page_count)

            cookies = copy.deepcopy(self.cookie)
            cookies["selectedStore"] = item["internalId"]
            for p in range(1, n_pages):
                params = copy.deepcopy(self.params)
                params["p"] = p
                req_item = [
                    res.url,
                    {
                        "categoryId": item["categoryId"],
                        "subcategoryId": item["subcategoryId"],
                        "storeId": item["storeId"],
                        "internalId": item["internalId"],
                        "url": res.url,
                    },
                    cookies,
                    params
                ]
                requests.append(req_item)

            # Print Progress
            if should_print:
                self.print_func(i, len(responses), "process responses liquorland 1")

        iteration = [0]
        responses = asyncio.run(req.create_async_tasks(requests,
                                                       {"printer": (self.print_func,
                                                                    len(requests) - 1,
                                                                    task + " 2",
                                                                    iteration)},
                                                       self._async_get_item_page))
        if should_print:
            self.print_func(0, len(responses), "process responses liquorland 2")

        for i, (item, res) in enumerate(responses):
            soup = BeautifulSoup(res.text(), features="html.parser")
            item_divs = soup.find_all("div", {"class": "productItemDisplay"})
            for item_div in item_divs:
                new_item = self._create_item(item_div, item)
                items.append(new_item)

            # Print Progress
            if should_print:
                self.print_func(i + 1, len(responses), "process responses liquorland 2")

        return items

    def _create_item(self, item_div, item):
        """
        Creates an item dict for new item
        :param item_div: Soup div object
        :param item: Item object from response
        :return: item
        """
        # Create new item dict and add to items list
        name, price, sale_price, image_url, barcode, stock, volume, url, sku = self._get_item_info(item_div)

        new_item = {
            "name": name,
            "barcode": barcode,
            "categoryId": item["categoryId"],
            "image_url": image_url,
            "price": price,
            "salePrice": sale_price,
            "stock": stock,
            "volumeEach": volume,
            "url": url,
            "internalSku": sku,
            "storeId": item["storeId"],
            "internalId": item["internalId"]
        }
        if item["subcategoryId"] is not None:
            new_item["subcategoryId"] = item["subcategoryId"]

        return new_item

    @staticmethod
    def _get_page_item_count(page):
        """
        Decodes item count on page
        :param page: BeautifulSoup html object
        :return: Integer count for total number products
        """
        count_div = page.find("div", {"class": "searchSortHeader"})
        count_str = count_div.find("span").getText()
        count_str = count_str.strip(" results")
        i = len(count_str) - 1
        while count_str[i].isnumeric():
            i -= 1
        i += 1

        return int(count_str[i:])

    def _get_item_info(self, item_div):
        """
        Decodes product information from html soup div
        :param item_div: BeautifulSoup div object
        :return: name, price, sale_price, image_url, barcode, stock, volume, url, sku
        """

        # Get name
        name_div = item_div.find("div", {"class": "w2mItemName"})
        name = name_div.a.getText()

        # Url
        url = f"{self.base_url}/{name_div.a['href']}"

        # Get prices
        price_span = item_div.find("span", {"class": "msrp"})
        if price_span is None:
            price_str = item_div.find("span", {"class": "value"}).getText()
            sale_price = None
        else:
            price_str = price_span.getText()
            sale_price_str = item_div.find("span", {"class": "SpecialPriceFormat2"}).getText()
            sale_price = float(sale_price_str.strip('$').replace(",", ''))
        price = float(price_str.strip("$").replace(",", ''))

        # Image
        image_div = item_div.find("div", {"class": "thumbnail"})
        image = image_div.find("img")
        image_url = f"{self.base_url}/{image['src']}"
        if image_url == "App_Themes/Liquorland/Images/no-thumbnail-available.png":
            image_url = None
            barcode = None
        else:
            # Ean
            barcode_index = image_url.find("ProductImages")
            barcode = tools.get_barcode(image_url[barcode_index + 16:barcode_index + 16 + 20])

        # Stock
        stock_text = item_div.find("span", {"class": "status"}).getText()
        stock = "o"
        if stock_text == "Stock High" or stock_text == "Stock Medium":
            stock = "i"
        elif stock_text == "Stock Low":
            stock = "l"

        # Volume
        volume = self._get_item_volume(name)

        # Internal Sku
        sku = self._get_item_sku(url)

        return name, price, sale_price, image_url, barcode, stock, volume, url, sku

    @staticmethod
    def _get_item_sku(url):
        """
        Decodes the item sku from url
        :param url: Url of product
        :return: sku as a string
        """
        url_strip = url.strip(".aspx")

        i = len(url_strip) - 1
        while url_strip[i].isnumeric():
            i -= 1
        return url_strip[i:]

    @staticmethod
    def _get_item_volume(name):
        """
        Get the volume from the end of a product name
        :param name: String name of the product
        :return: Integer value of volume in mls
        """
        try:
            # Find units
            if name[-2:] == "Lt":
                unit = "L"
                name = name[:-2]
            elif name[-2:] == "ml" or name[-2:] == "ML":
                unit = "ml"
                name = name[:-2]
            elif name[-1] == "L" or name[-1] == "l":
                unit = "L"
                name = name[:-1]
            elif name[-1] == "m" and (name[-2].isnumeric() or name[-2] == " "):
                unit = "ml"
                name = name[:-1]
            else:
                return None

            # Get numeric bit
            name = name.strip(" ")
            i = len(name) - 1
            while name[i].isnumeric() or name[i] == ".":
                i -= 1

            # Convert to mls
            amount = float(name[i+1:])
            if unit == "L":
                amount = amount * 1000

            return int(amount)
        except Exception:
            return None

    @staticmethod
    async def _async_get_item_page(session, url, item, cookies, params, printer=None):
        """
        Gets Item page using session
        :param session: Session for request
        :param url: Url for http get request
        :param item: Dict item object to get returned with response
        :param cookies: Cookies for http request
        :param printer: (print_func, total, task, iteration) tuple
        :param params: Params for http request
        :return: (item, res) tuple, custom Response object
        """
        async with session.get(url, cookies=cookies, params=params) as res:
            text = await res.text()
            new_res = req.Response(res, None, {}, None, text)
            if printer is not None:
                print_func, total, task, iteration = printer
                print_func(iteration[0], total, task)
                iteration[0] += 1
            return item, new_res


