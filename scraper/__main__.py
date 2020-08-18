import sys
from stores import countdown, liquorland
import api

STORE_DICT = {
    "countdown": countdown.Countdown,
    "liquorland": liquorland.controller.Liquorland
}


def main():
    args = sys.argv[1:]
    store_name = args[1]
    if args[0] == 'scrape':
        scrape(store_name)
    elif args[0] == 'find_stores':
        find_stores(store_name)


def scrape(store_name):
    store_class = STORE_DICT[store_name]
    store = store_class()
    store.update_all_items()


def find_stores(store_name):
    store_class = STORE_DICT[store_name]
    store = store_class()
    store.update_locations()


def scrape_all():
    cd = countdown.Countdown()
    cd.update_locations()


if __name__ == '__main__':
    main()

