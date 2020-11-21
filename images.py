from PIL import Image, ImageChops, ImageOps
from io import BytesIO
import requests
import copy


def trim(im, border):
    bg = Image.new(im.mode, im.size, border)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def is_white(r, b, g, tolerance):
    return (255 * 3 - tolerance) < (r + b + g) <= (255 * 3)


def cut():
    res = requests.get('https://storage.googleapis.com/pisspricer-bucket-dev/items/18496.jpeg')
    filePath = '~/Desktop/image4.png'

    # Get image
    image = Image.open(BytesIO(res.content))
    width, height = image.size
    img = image.convert("RGBA")
    datas = list(img.getdata())

    print(width, height)

    newData = []
    tolerance = 40

    left = []
    right = []
    top_index = 0
    bottom_index = height - 1

    is_above = True
    is_in = False

    # Iterates through each row, setting pixels left and right of the image that are white to transperant
    for h in range(0, height):
        row = datas[(width * h):(width * (h+1))]
        new_row = copy.deepcopy(row)

        # Left -> Right
        for i, pixel in enumerate(row):
            r, b, g, a = pixel
            if is_white(r, b, g, tolerance):
                new_row[i] = (255, 255, 255, 0)
            else:
                left.append(i)
                if i == (width - 1):
                    if is_above:
                        is_in = True
                        is_above = False
                        top_index = 0 if h == 0 else h - 1
                    if is_in:
                        # Bottom
                        is_in = False
                        bottom_index = (height - 1) if h == (height - 1) else h + 1
                break

        # Right -> Left
        for i in range(width - 1, -1, -1):
            r, b, g, a = row[i]
            if is_white(r, b, g, tolerance):
                new_row[i] = (255, 255, 255, 0)
            else:
                right.append(i)
                break

        newData.append(new_row)

    newSData = []
    for row in newData:
        newSData += row

    img.putdata(newSData)

    img.show()
    # cropped.save(filePath)


if __name__ == '__main__':
    cut()
