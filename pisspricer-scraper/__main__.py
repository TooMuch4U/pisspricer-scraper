import sys
from stores import countdown, liquorland, henrys
import api

STORE_DICT = {
    "countdown": countdown.Countdown,
    "liquorland": liquorland.controller.Liquorland,
    "henrys": henrys.Henrys
}


def main():
    args = sys.argv[1:]
    if args[0] == 'scrape-all':
        scrape_all()
    else:
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
    for store_class in STORE_DICT.values():
        try:
            store_scraper = store_class()
            store_scraper.update_all_items()
        except Exception as err:
            print(f"\n\n{err}\n\n")


if __name__ == '__main__':
    main()

