import custom_requests as req


class Model:

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
            try:
                json = await response.json()
            except Exception:
                json = None
            try:
                text = await response.text()
            except Exception:
                text = None
            return item, req.Response(response, None, None, json, text, read=image)