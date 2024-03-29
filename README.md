# Pisspricer Scraper CLI
A Python CLI application used to scrape, process and upload liquor prices for pisspricer.

# Requirements
- git
- Python3
- pip

# Install / Setup
1. Clone the repository.
	```bash
	git clone https://github.com/TooMuch4U/pisspricer-scraper
	```
2. Install pip dependencies.
	```bash
	pip install -r requirements.txt
	```
3. Set the following environment variables.
	```
	pisspricer.url=http://api.pisspricer.co.nz/api/v1
	pisspricer.email=api@pisspricer.co.nz
	pisspricer.password=pword
	maps_api_key=maps_api_key
	```

# Usage
A single stores prices can be updated using
```bash
python3 pisspricer-scraper scrape <store_name>
```

The prices of all stores can be updated using
```bash
python3 pisspricer-scraper scrape-all
``` 

The store locations for a store can be updated with
```bash
python3 pisspricer-scraper find_stores <store_name>
```

# Automated Scraping
A crontab job can be setup to run the scraping script each day. The following will scrape all stores at 4:00am each morning. 
1. Edit the crontab.
	```bash
	crontab -e
	```
2. Paste the following at the bottom of the file.
	```bash
	0 4 * * * /pathtorepo/pisspricer-scraper/venv/bin/python /pathtorepo/pisspricer-scraper/pisspricer-scraper scrape-all > ~/cron.log 2>&1
	```
Note: a python binary in a virtual environment is being used, and the output is being written to a log file.

