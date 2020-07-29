import sys
from stores import countdown
import api

STORE_DICT = {"countdown": countdown.Countdown}


def main():
    args = sys.argv[1:]
    store_name = args[1]
    if args[0] == 'scrape':
        scrape(store_name)


def scrape(store_name):
    store_class = STORE_DICT[store_name]
    store = store_class()
    store.update_all_items()


def scrape_all():
    cd = countdown.Countdown()
    cd.update_locations()


if __name__ == '__main__':
    main()

