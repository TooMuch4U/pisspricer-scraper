import aiohttp
import asyncio
import time
import pandas as pd
import requests

import tools
import copy


async def async_get(session, url, headers={}, cookies={}):
    """Execute an http call async
    Args:
        session: context for making the http call
        url: URL to call
        headers: optional headers
        cookies: option cookies
    Return:
        responses: A dict like object containing http response
    """
    url_string = url["url"]
    carry = url.get("carry", None)
    async with session.get(url_string, headers=headers, cookies=cookies) as response:
        resp = await response.json()
        resp["carry"] = carry
        return resp


async def create_async_get_list(urls, header, cookie):
    """ Gather many HTTP call made async
    Args:
        urls: a list of string
        header: header to use in all requests
        cookie: cookie to use in all requests
    Return:
        responses: A list of dict like object containing http response
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(
                async_get(
                    session,
                    url,
                    headers=header,
                    cookies=cookie
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses


def async_get_list(urls, headers={}, cookies={}):
    """
    Async get a list of urls

    :param urls: List of dicts {"url": url, "carry}
    :param headers: Header to be used for each request
    :param cookies: Cookie to be used for each request
    :return: List of responses
    """
    responses = asyncio.run(create_async_get_list(urls, headers, cookies))
    return responses


""" -----------
POSTING ITEMS
---------------"""


async def async_post(session, url, payload, headers={}, cookies={}, printer=None, iteration=None):
    """
    Execute http post request
    :param session: Session for requests
    :param url: Url for http requests
    :param payload: json payload for request
    :param headers: HTTP Header for request
    :param cookies: HTTP cookies for request
    :param printer: (print_function, total, title) for printing
    :param iteration: [int] list with int for counting print number
    :return: None
    """
    async with session.post(url, headers=headers, cookies=cookies, json=payload) as response:
        try:

            if printer is not None:
                print_function, total, task = printer
                iteration[0] += 1
                print_function(iteration[0], total, task)
            if response.status != 201:
                raise Exception("Error while posting item: " + str(response))
            resp = await response.json()
            return resp
        except Exception as err:
            tools.log_error(err)
            raise err


async def create_async_post_list(reqs, printer):
    """
    Gather http async calls
    :param reqs: List of (payload, url, header, cookie) tuples for requests
    :param printer: (print_function, total, title) for printing
    :return: List of json response items
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        iteration = [0]
        for payload, url, header, cookie in reqs:
            tasks.append(
                async_post(
                    session,
                    url,
                    payload,
                    headers=header,
                    cookies=cookie,
                    printer=printer,
                    iteration=iteration
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses


def async_post_items(payloads, url, headers={}, cookies={}, printer=None):
    """
    Async post a list of items
    :param payloads: List of items to post
    :param url: Url to post to
    :param headers: HTTP headers
    :param cookies: HTTP cookies
    :param printer: (print_function, total, title) for printing
    :return: Return list of json response objects
    """
    reqs = []
    for payload in payloads:
        reqs.append((payload, url, headers, cookies,))
    responses = asyncio.run(create_async_post_list(reqs, printer))
    return responses


""" -----------
GETTING IMAGES
---------------"""


async def async_get_image(session, sku, url, printer=None, iteration=None):

    async with session.get(url) as response:
        if printer is not None:
            print_function, total, task = printer
            iteration[0] += 1
            print_function(iteration[0], total, task)
        image = await response.read()
        return sku, image


async def create_async_get_images(reqs, printer):
    """
    Gather http async calls
    :param reqs: List of (payload, url, header, cookie) tuples for requests
    :param printer: (print_function, total, title) for printing
    :return: List of json response items
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        iteration = [0]
        for sku, url in reqs:
            tasks.append(
                async_get_image(
                    session,
                    sku,
                    url,
                    iteration=iteration
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses


def async_get_images(image_urls, printer=None):
    """
    Gets all images
    :param image_urls: List of tuples (sku, image_url)
    :param printer: (print_function, total, title)
    :return: (sku, image) tuples
    """
    images = asyncio.run(create_async_get_images(image_urls, printer))
    return images


""" -----------
POSTING IMAGES
---------------"""


async def async_post_image(session, url, image, headers={}, cookies={}, printer=None, iteration=None):
    """
    Execute http post request
    :param session: Session for requests
    :param url: Url for http requests
    :param image: Image data
    :param headers: HTTP Header for request
    :param cookies: HTTP cookies for request
    :param printer: (print_function, total, title) for printing
    :param iteration: [int] list with int for counting print number
    :return: None
    """
    async with session.put(url, headers=headers, cookies=cookies, data=image) as response:
        try:

            if printer is not None:
                print_function, total, task = printer
                iteration[0] += 1
                print_function(iteration[0], total, task)
            if response.status != 201 and response.status != 200:
                raise Exception("Error while posting image: " + str(response))
            return response
        except Exception as err:
            tools.log_error(err)
            raise err


async def create_async_post_images(reqs, printer):
    """
    Gather http async calls
    :param reqs: List of (payload, url, header, cookie) tuples for requests
    :param printer: (print_function, total, title) for printing
    :return: List of json response items
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        iteration = [0]
        for image, url, headers in reqs:
            tasks.append(
                async_post_image(
                    session,
                    url,
                    image,
                    headers=headers,
                    iteration=iteration,
                    printer=printer
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses


def post_images(images, base_url, headers={}, printer=None):
    """
    Posts images to pisspricer api to url '{base_url}/{id}/image'
    :param images: List of (id, image) tuples
    :param base_url: Base url for posting
    :param headers: Dictionary of headers
    :param printer: (print_function, total, title)
    :return: List of responses
    """
    reqs = []
    new_headers = copy.deepcopy(headers)
    new_headers["Content-Type"] = "image/jpeg"
    for id, image in images:
        url = f"{base_url}/{id}/image"
        reqs.append((image, url, new_headers))
    responses = asyncio.run(create_async_post_images(reqs, printer))
    return responses


""" -----------
POSTING PRICES
---------------"""


async def async_put_json(session, url, payload, total=0, headers={}, cookies={}, stop_print=False, iteration=None):
    """
    Execute http put requests using an aiohttp session.
    :param session: Aiohttp session
    :param url: Url for http request
    :param payload: Json data for request
    :param total: Total number of requests for printing
    :param headers: Headers for http request
    :param cookies: Cookies for http request
    :param stop_print: Boolean, true to disabling printing
    :param iteration: List with single integer for counting current iteration
    :return: None
    """
    try:
        async with session.put(url, headers=headers, cookies=cookies, json=payload) as response:
            iteration[0] += 1
            if not stop_print:
                print(f"{iteration[0]}/{total}", end="\r")
            code = response.status
            return str(code)
    except asyncio.TimeoutError:
        return "Timeout"


async def create_async_tasks(arg_list, kwargs, func, timeout_mins=20):
    """
    Creates a list of async tasks using function and keywords given
    :param arg_list: List of argument tuples to be using in function
    :param kwargs: Dictionary of keyword args to be used in all requests
    :param func: Function for args to be used in
    :param timeout_mins: Timeout values for whole async operation in minutes
    :return: List of responses from function
    """
    timeout = aiohttp.ClientTimeout(total=timeout_mins*60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for args in arg_list:
            tasks.append(func(session, *args, **kwargs))
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses


def put_prices(prices, base_url, headers={}):
    """
    Puts prices using async function
    :param prices: List of (sku, store_id, price_data) tuples
    :param base_url: Base url to be used in req urls, '{base_url}/items/{sku}/stores/{store_id}'
    :param headers: Headers to be used in all requests
    :return: None
    """
    print("Starting upload price data...")

    # Create a list of args
    args = []
    for sku, store_id, price_data in prices:
        url = f"{base_url}/items/{sku}/stores/{store_id}"
        args.append((url, price_data))

    # Create keyword args
    iteration = [0]
    kwargs = {
        "headers": headers,
        "total": len(args),
        "iteration": iteration
    }

    # Run and time
    time1 = time.time()
    responses = asyncio.run(create_async_tasks(args, kwargs, async_put_json))
    time2 = time.time()

    # Print results
    print(f'Took {time2 - time1:.2f} s')
    print(pd.Series(responses).value_counts())


def get(url, cookies={}, headers={}, params={}):
    """
    Simple http get request using aiohttp
    :param params: Dict of query parameters
    :param url: Url string from http request
    :param cookies: Dict of cookies
    :param headers: Dict of headers
    :return: Aiohttp response object
    """

    async def async_get(u, c, h, p):
        async with aiohttp.ClientSession() as session:
            async with session.get(u, cookies=c, headers=h, params=p) as resp:
                heads, json, body = await Response.build_params(resp)
                return resp, heads, json, body

    resp, heads1, json1, body1 = asyncio.run(async_get(url, cookies, headers, params))
    return Response(resp, None, heads1, json1, body1)


def post(url, payload, cookies={}, headers={}, params={}):
    """
    Simple http post request for json data using aiohttp
    :param url: Url string for http request
    :param payload: Json dict object to post
    :param cookies: Dict of cookies
    :param headers: Dict of headers
    :param params: Dict of params
    :return: Aiohttp response object
    """

    async def async_post(url2, payload2, cookies2, headers2, params2):
        async with aiohttp.ClientSession() as session:
            async with session.post(url2, json=payload2, cookies=cookies2, headers=headers2, params=params2) as resp:
                heads1, json1, body1 = await Response.build_params(resp)
                return resp, heads1, json1, body1

    resp, heads, json, body = asyncio.run(async_post(url, payload, cookies, headers, params))
    return Response(resp, payload, heads, json, body)


class Response:

    def __init__(self, aio_res, payload, headers, json, text, read=None):
        self.res = aio_res
        self.status = aio_res.status
        self.url = aio_res.url
        self.headers = headers
        self._text = text
        self._json = json
        self.content = payload
        self._read = read

    def json(self):
        return self._json

    def text(self):
        return self._text

    def read(self):
        return self._read

    @staticmethod
    async def build_params(res):
        headers = res.headers
        json = None
        body = None
        if 200 <= res.status <= 299:
            json = await res.json()
            body = await res.text()
        return headers, json, body

