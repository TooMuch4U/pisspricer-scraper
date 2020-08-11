import aiohttp
import asyncio
import aiofiles
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


async def async_put_json(session, url, payload, headers={}, cookies={}, printer=None, iteration=None):
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
    async with session.put(url, headers=headers, cookies=cookies, json=payload) as response:
        if printer is not None:
            print_function, total, task = printer
            iteration[0] += 1
            print_function(iteration[0], total, task)
        if response.status != 201 and response.status != 200:
            tools.log_error(Exception("Error while putting json: " + str(response)))
        return response


async def create_async_put_json(reqs, printer):
    """
    Gather http async calls
    :param reqs: List of (payload, url, header, cookie) tuples for requests
    :param printer: (print_function, total, title) for printing
    :return: List of response items
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        iteration = [0]
        for payload, url, headers, cookies in reqs:
            tasks.append(
                async_put_json(
                    session,
                    url,
                    payload,
                    headers=headers,
                    cookies=cookies,
                    iteration=iteration,
                    printer=printer
                )
            )
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses


def put_prices(prices, base_url, headers={}, printer=None):
    """
    Puts price data to "{base_url}/items/{sku}/stores/{store_id}"
    :param prices: List of (sku, store_id, price_data) tuples
    :param base_url: Base url for posting
    :param headers: Dictionary of headers
    :param printer: (print_function, total, title)
    :return: List of responses
    """
    print("Starting upload price data...")
    reqs = []
    for sku, store_id, price_data in prices:
        url = f"{base_url}/items/{sku}/stores/{store_id}"
        reqs.append((price_data, url, headers, {}))
    # Print initial print if possible
    if printer is not None:
        print_function, total, task = printer
        print_function(0, len(prices), task)

    # responses = asyncio.run(create_async_put_json(reqs, printer))
    test_put_json(reqs, printer)
    return []




import pandas as pd
import concurrent.futures
import requests
import time


def load_url(url, payload, timeout, headers={}, cookies={}):
    ans = requests.put(url, headers=headers, cookies=cookies, json=payload, timeout=timeout)
    return ans.status_code


def test_put_json(reqs, printer):
    out = []
    CONNECTIONS = 200
    TIMEOUT = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
        future_to_url = (executor.submit(load_url, url, payload, TIMEOUT, headers, cookies)
                         for payload, url, headers, cookies in reqs)
        time1 = time.time()
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
            except Exception as exc:
                data = str(type(exc))
            finally:
                out.append(data)

                if printer is not None:
                    print_function, total, task = printer
                    print_function(len(out), total, task)
                else:
                    print(f"{str(len(out))}/{len(reqs)}", end="\r")
                    #print('{:.1f}%'.format(100 * len(out)/len(reqs)), end="\r")

        time2 = time.time()

    print(f'Took {time2-time1:.2f} s')
    print(pd.Series(out).value_counts())

