
class ApiException(Exception):

    def __init__(self, res, task, api_name):
        message = f"Error using {api_name} API while {task}. A response code of {res.status_code} was returned."
        super().__init__(message)


class PisspricerApiException(ApiException):

    NAME = "Pisspricer"

    def __init__(self, res, task):
        super().__init__(res, task, self.NAME)


class CountdownApiException(ApiException):

    NAME = "Countdown"

    def __init__(self, res, task):
        super().__init__(res, task, self.NAME)


class GoogleApiException(ApiException):

    NAME = "Google"

    def __init__(self, res, task):
        super().__init__(res, task, self.NAME)


class AiohttpException(Exception):

    def __init__(self, res, task, name):
        message = f"Error while '{task}' for '{name}'. Status: {res.status}, Url {res.url}, Content: {res.content}"
        super().__init__(message)


class LiquorlandException(AiohttpException):

    NAME = "Liquorland"

    def __init__(self, res, task):
        self.res = res
        super().__init__(res, task, self.NAME)

