import sys
from stores import countdown
import api



def main():
    args = sys.argv[1:]
    if args[0] == 'scrape':
        scrape_all()


def scrape_all():
    cd = countdown.Countdown()
    cd.update_locations()


if __name__ == '__main__':
    main()

