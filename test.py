from pisspricer import Pisspricer

if __name__ == '__main__':
    import api
    items = [{'sku': 14764, 'image_url': 'https://static.countdown.co.nz/assets/product-images/big/9421901182038.jpg'}]

    pisspricer = Pisspricer(api)
    pisspricer.upload_new_images(items, print)
