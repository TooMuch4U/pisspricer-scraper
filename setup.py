from setuptools import setup
setup(
    name = 'pisspricer-scraper',
    version = '0.1.0',
    packages = ['scraper'],
    entry_points = {
        'console_scripts': [
            'scraper = scraper.__main__:main'
        ]
    })