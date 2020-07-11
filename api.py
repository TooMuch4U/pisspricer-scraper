import os
import requests
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

global url
global token
url = os.getenv('pisspricer.url')
email = os.environ.get('pisspricer.email')
password = os.environ.get('pisspricer.password')
print("url: {}".format(url))

res = requests.post(url + '/users/login', json={"email": email, "password": password})
if res.status_code != 200:
    raise Exception("Connection to API failed")
res_json = res.json()
token = res_json["authToken"]