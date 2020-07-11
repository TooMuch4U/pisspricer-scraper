import sys
from .countdown import Countdown
import api


def main():
    print('in main')
    args = sys.argv[1:]
    print('count of args :: {}'.format(len(args)))
    for arg in args:
        print('passed argument :: {}'.format(arg))
    if args[0] == 'scrape':
        print("scrape")
        print("API Key: {}".format(api.token))


def scrape_all():
    store = Countdown()
    store.start()


if __name__ == '__main__':
    main()

