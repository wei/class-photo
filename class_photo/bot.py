import discord
from discord.ext import commands
import os
from PIL import Image
import requests
from io import BytesIO
from dotenv import load_dotenv
from . import face

bot = commands.Bot('-cp')

def main():
    load_dotenv()
    bot.run(os.getenv("TOKEN"))

@bot.event
async def on_ready():
    print('Bot Online!')
    urls = await get_photos()
    await bot.logout()
    face.crop(urls)


async def get_photos():

    urls = await get_all_urls()
    print(f"Collected {len(urls)} photo urls in total")

    for url in urls:
        await save_photo(url)

    print(f"Saved all {len(urls)} photos!")
    return urls

async def get_all_urls():
    urls = []
    selfie_channel = bot.get_channel(int(os.getenv("CHANNEL")))
    messages = await selfie_channel.history(limit=200).flatten()

    for message in messages:
        if len(message.attachments) > 0:
            urls.append((message.attachments[0].url, message.id))
    return urls

async def save_photo(url):
    print(f'Download & process {url[0]}')

    try:
        response = requests.get(url[0], timeout=5)
        try:
            try:
                os.mkdir("img")
                os.mkdir("img/discord")
            except FileExistsError:
                pass
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image = rotate_if_exif_specifies(image)
            image.convert('RGB').save(f"img/discord/{url[1]}.jpg", optimize=True)
            print(f"Saved photo as {url[1]}.jpg")

        except requests.HTTPError:
            print('HTTP error')

    except requests.exceptions.ConnectionError:
        print('Network error')

def rotate_if_exif_specifies(image):
    try:
        exif_tags = image._getexif()
        if exif_tags is None:
            # No EXIF tags, so we don't need to rotate
            print('No EXIF data, so not transforming')
            return image

        value = exif_tags[274]
    except KeyError:
        # No rotation tag present, so we don't need to rotate
        print('EXIF data present but no rotation tag, so not transforming')
        return image

    value_to_transform = {
        1: (0, False),
        2: (0, True),
        3: (180, False),
        4: (180, True),
        5: (-90, True),
        6: (-90, False),
        7: (90, True),
        8: (90, False)
    }

    try:
        angle, flip = value_to_transform[value]
    except KeyError:
        print(f'EXIF rotation \'{value}\' unknown, not transforming')
        return image

    print(f'EXIF rotation \'{value}\' detected, rotating {angle} degrees, flip: {flip}')
    if angle != 0:
        image = image.rotate(angle)

    if flip:
        image = image.tranpose(Image.FLIP_LEFT_RIGHT)

    return image