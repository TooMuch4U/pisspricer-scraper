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


def process_response_content(content):
    """
    Processes a response content
    :param content: Content from a response
    :return: Image content
    """
    image = Image.open(BytesIO(content))
    return process_image(image)


def remove_background(pixel_list, width, height, tolerance=100):
    """
    Iterates through each row, setting pixels left and right of the image that are white to transperant
    :param height: Height of image
    :param width: Width of image
    :param tolerance: Tolerance for checking if a pixel is white
    :param pixel_list: List of (R, B, G, A) pixels
    :return: 2-tuple (box, new_pixel_list)
    """
    new_rows = []

    left = []
    right = []
    top_index = 0
    bottom_index = height - 1

    is_above = True
    is_in = False

    # Iterate through rows
    for h in range(0, height):
        row = pixel_list[(width * h):(width * (h + 1))]
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
                        # Top
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

        new_rows.append(new_row)

    # Convert row list into list of pixels
    new_pixels = []
    for row in new_rows:
        new_pixels += row

    # Create box
    box = (min(left), top_index, max(right), bottom_index)

    return box, new_pixels


def process_image(image):
    """
    Processes an item image: Removes the background, and crops to the sides of the item
    :param image: PIL.Image object
    :return: PIL.Image
    """
    # Get image details
    width, height = image.size

    # Convert to RBGA, then convert to list of pixels
    img = image.convert("RGBA")
    pixel_list = list(img.getdata())

    # Remove image background
    box, new_pixels = remove_background(pixel_list, width, height)

    # Set data for image
    img.putdata(new_pixels)

    # Crop image
    img = img.crop(box)

    img.show()
    # cropped.save(filePath)


if __name__ == '__main__':
    res = requests.get('https://storage.googleapis.com/pisspricer-bucket-dev/items/18496.jpeg')
    process_response_content(res.content)
