import aiohttp
import asyncio
import custom_exceptions
import custom_requests as req
import tools
import images


class Pisspricer:

    def __init__(self, api):
        self.api = api

    def upload_new_stores(self, locations, brand_id, printer=None):
        """
        Posts stores to pisspricer api that are new (based on internal id).
        Gets data from google maps api if location data is incomplete.
        Uploads region if it doesn't already exist.
        :param printer: (print_function, total, title) for printing
        :param brand_id: Brand id of store locations
        :param locations: List of dict objects
            {
                name: "required|string",
                url: "required|string",
                region: "required|string",
                region_lat: "numeric",
                region_lng: "numeric",
                address: "required|string",
                postcode: "numeric",
                lattitude: "numeric",
                longitude: "numeric"
                internalId: "string"
            }
        :return: None
        """
        # Get current locations
        cur_locations_res = req.get(self.api.url + "/stores",
                                    headers=self.api.headers,
                                    params={"brandId": brand_id})
        if cur_locations_res.status != 200:
            raise custom_exceptions.AiohttpException(cur_locations_res, "get stores", "pisspricer")
        cur_locations = cur_locations_res.json()

        # Create a set of internal ids
        cur_locs_set = set()
        for loc in cur_locations:
            cur_locs_set.add(loc["internalId"])

        # Get a list of regions
        regions = self.get_regions()

        # Print first iteration
        if printer is not None:
            print_func, total, task = printer
            print_func(0, total, task)

        # Create a list of new stores
        new_locations = []
        for i, loc in enumerate(locations):
            try:
                # Check if the store is new
                if loc["internalId"] not in cur_locs_set:

                    # Get location if data not supplied
                    region = loc["region"]
                    lat = loc["lattitude"]
                    lng = loc["longitude"]
                    postcode = loc["postcode"]
                    address = loc["address"]
                    location_list = [region, lat, lng, postcode, address]
                    if any(item is None for item in location_list):
                        lat, lng, address, postcode, region = tools.geocode_address(f"{loc['name']}, {address}")

                    # Create new location dict
                    new_loc = {
                        "name": loc["name"],
                        "url": loc["url"],
                        "brandId": brand_id,
                        "regionId": self._get_region_id(regions, region, lat=loc["region_lat"], lng=loc["region_lng"]),
                        "lattitude": lat,
                        "longitude": lng,
                        "postcode": postcode,
                        "address": address,
                        "internalId": loc["internalId"]
                    }

                    # Add new store to task list
                    new_locations.append([self.api.url + "/stores", new_loc])

            except custom_exceptions.GoogleApiException as err:
                tools.log_error(err)
            except custom_exceptions.AiohttpException as err:
                tools.log_error(err)
            finally:
                if printer is not None:
                    print_func(i+1, total, task)

        # Post all stores
        # TODO Change post function
        iteration = [0]
        print_func, _, task = printer
        kwargs = {"headers": self.api.headers,
                  "printer": (print_func, len(new_locations), task),
                  "iteration": iteration}
        responses = asyncio.run(req.create_async_tasks(new_locations, kwargs, self._async_post_json))
        for res in responses:
            if res.status != 201:
                tools.log_error(custom_exceptions.AiohttpException(res, "post stores", "pisspricer"))

    @staticmethod
    async def _async_post_json(session, url, payload, headers={}, cookies={}, params={}, printer=None, iteration=None):
        """
        Execute http put requests using an aiohttp session.
        :param session: Aiohttp session
        :param url: Url for http request
        :param payload: Json data for request
        :param headers: Headers for http request
        :param cookies: Cookies for http request
        :param printer: (print_func, total, task) for printing
        :param iteration: List with single integer for counting current iteration
        :return: Custom response object
        """
        async with session.post(url, headers=headers, cookies=cookies, json=payload, params=params) as response:
            if printer is not None and iteration is not None:
                iteration[0] += 1
                print_func, total, task = printer
                print_func(iteration[0], total, task)
            heads1, json1, body1 = await req.Response.build_params(response)
            return req.Response(response, payload, heads1, json1, body1)

    @staticmethod
    async def _async_put_json(session, url, payload, headers={}, cookies={}, params={}, printer=None, iteration=None):
        """
        Execute http put requests using an aiohttp session.
        :param session: Aiohttp session
        :param url: Url for http request
        :param payload: Json data for request
        :param headers: Headers for http request
        :param cookies: Cookies for http request
        :param printer: (print_func, total, task) for printing
        :param iteration: List with single integer for counting current iteration
        :return: Custom response object
        """
        async with session.put(url, headers=headers, cookies=cookies, json=payload, params=params) as response:
            if printer is not None and iteration is not None:
                iteration[0] += 1
                print_func, total, task = printer
                print_func(iteration[0], total, task)
            heads1, json1, body1 = None, None, None
            return req.Response(response, payload, heads1, json1, body1)

    @staticmethod
    async def _async_get(session, url, item, headers={}, cookies={}, params={}, printer=None, iteration=None):
        """
        Execute http get requests using an aiohttp session.
        :param session: Aiohttp session
        :param url: Url for http request
        :param headers: Headers for http request
        :param cookies: Cookies for http request
        :param printer: (print_func, total, task) for printing
        :param iteration: List with single integer for counting current iteration
        :return: Custom response object
        """
        async with session.get(url, headers=headers, cookies=cookies, params=params) as response:
            if printer is not None and iteration is not None:
                iteration[0] += 1
                print_func, total, task = printer
                print_func(iteration[0], total, task)
            image = await response.read()
            return item, req.Response(response, None, None, None, None, read=image)

    def _get_region_id(self, regions, region_name, lat=None, lng=None):
        """
        Gets the id of an existing region, or creates a region if it doesn't exist.
        :param regions: List of regions from pisspricer api
        :param region_name: Name of region as a string
        :return: Region id integer
        """
        region_id = None
        for region in regions:
            if region["name"] == region_name.capitalize():
                region_id = region["regionId"]
                break

        if region_id is None:

            # Post new region
            payload = {"name": region_name.capitalize()}
            if lat is not None:
                payload["lattitude"] = lat
                payload["longitude"] = lng
            res = req.post(self.api.url + "/regions",
                           payload,
                           headers=self.api.headers)

            # Check success
            if res.status != 201:
                raise custom_exceptions.AiohttpException(res, "_get_region_id", "liquorland")

            # Get created regionId
            region_id = res.json()["regionId"]

            # Add new region to regions list
            new_region = {
                "regionId": region_id,
                "name": payload["name"],
                "lattitude": lat,
                "longitude": lng
            }
            regions.append(new_region)

        return region_id

    def get_regions(self):
        """
        Get a list of regions from pisspricer api
        :return: List of region dict objects from pisspricer api
        """
        regions_res = req.get(self.api.url + "/regions",
                              headers=self.api.headers)
        if regions_res.status != 200:
            raise custom_exceptions.AiohttpException(regions_res, "get_regions", "pisspricer")
        regions = regions_res.json()

        return regions

    def get_stores(self, brand_id=None):
        """
        Get json stores from pisspricer api
        :param brand_id: Optional brand id filter
        :return: List of json objects
        """
        params = {}
        if brand_id is not None:
            params = {"brandId": brand_id}
        res = req.get(self.api.url + "/stores", headers=self.api.headers, params=params)
        return res.json()

    def update_item_prices(self, items, brand_id, brand_name, print_func=None):
        """
        Posts items to pisspricer api that are new
        :param items: List of dict items
            {
                "name"
                "categoryId"
                "subcategoryId"
                "internalId"
                "barcode"
                "storeId"
            }
        :param brand_id: Store brand id
        :param print_func: Function for printing
        :return: None
        """
        barcodes = req.get(self.api.url + "/barcodes", headers=self.api.headers)
        skus = req.get(self.api.url + "/internalids", headers=self.api.headers, params={"brandId": brand_id})
        barcodes = barcodes.json()
        skus = skus.json()

        requests = []
        for item in items:
            if item.get("barcode", None) is not None:
                barcode = item["barcode"]
                if barcode not in barcodes:
                    # Add item to requests list
                    requests.append([self.api.url + "/items",
                                     item])
                    barcodes[barcode] = []
            elif item.get("internalSku", None) is None or item.get("internalSku", None) not in skus:
                requests.append([self.api.url + "/items",
                                 item])
                skus[item["internalSku"]] = []

        # Post all items
        iteration = [0]
        if print_func is not None and len(requests) > 0:
            print_func(0, len(requests), "create new products")
        responses = asyncio.run(req.create_async_tasks(requests,
                                           {"headers": self.api.headers,
                                            "printer": (print_func, len(requests), "create new products"),
                                            "iteration": iteration},
                                           self._async_post_json))

        # Add new items to dictionaries
        for res in responses:
            if res.status == 200 or res.status == 201:
                data = res.json()
                new_sku = data["sku"]
                item = res.content
                barcode = item.get("barcode", None)
                if barcode is not None:
                    barcodes[barcode] = [new_sku]
                else:
                    skus[item["internalSku"]] = [new_sku]

        # Create request list for prices
        requests = []
        for item in items:

            if item.get("barcode") is not None:
                sku = barcodes[item["barcode"]][0]
            else:
                sku = skus[item["internalSku"]][0]
            item["sku"] = sku
            requests.append([f"{self.api.url}/items/{sku}/stores/{item['storeId']}",
                             item])

        # Upload images
        self.upload_new_images(items, print_func)

        # Put prices
        iteration = [0]
        if print_func is not None:
            print_func(0, len(requests), "post new prices")
        reses = asyncio.run(req.create_async_tasks(requests,
                                           {"headers": self.api.headers,
                                            "printer": (print_func, len(requests), "post new prices"),
                                            "iteration": iteration}, self._async_put_json))
        return reses

    def upload_new_images(self, items, print_func):
        """
        Uploads images for items that don't have one
        :param items: List of item dict objects. {"sku": int, "image_url": string}
        :return: None
        """
        all_items = req.get(self.api.url + "/allitems", headers=self.api.headers).json()
        print('start')

        # Iterate through items and add to get list if there isn't an image
        req_list = []

        checked_skus = set()
        for item in items:
            if item["sku"] not in checked_skus:

                has_image = True
                for cur_item in all_items:
                    if cur_item["sku"] == item["sku"]:
                        # Check if item doesn't have an image
                        if cur_item["hasImage"] == 0:
                            has_image = False
                        break
                if not has_image:

                    # Item doesn't have image
                    req_list.append([
                        item["image_url"],
                        item
                    ])

                # Add sku to set
                checked_skus.add(item["sku"])

        # Get images
        iteration = [0]
        if len(req_list) > 0:
            print_func(0, len(req_list), "get images")
        responses = asyncio.run(
            req.create_async_tasks(req_list,
                                   {"headers": self.api.headers,
                                    "printer": (print_func, len(req_list), "get images"),
                                    "iteration": iteration},
                                   self._async_get))

        # Create put image request list
        image_list = []
        print_func(0, len(responses), 'processing images')
        for i, (item, res) in enumerate(responses):
            try:
                content = res.read()
                image_bytes = images.process_response_content(content)
                image_list.append((item["sku"], image_bytes))
            except Exception as err:
                tools.log_error(err)
            finally:
                print_func(i + 1, len(responses))

        if len(image_list) > 0:
            print_func(0, len(image_list), "put images")
        responses = req.post_images(image_list,
                                    self.api.url + "/items",
                                    headers=self.api.headers,
                                    printer=(print_func, len(image_list), "put images"))




