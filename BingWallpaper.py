import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from string import Template

import requests
from PIL import Image

BING_URL = 'https://cn.bing.com/'
BING_IMAGE_URL = BING_URL + 'HPImageArchive.aspx'
BING_PARAMS = {'format': 'js', 'idx': '0', 'n': '1', 'mkt': 'zh-CN'}

TZ_SHANGHAI = timezone(timedelta(hours=8), name='Asia/Shanghai')
TODAY = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(TZ_SHANGHAI)

HEXO_SOURCE_DIR = 'source'
HEXO_IMAGE_DIR = HEXO_SOURCE_DIR + '/images'
HEXO_THUMB_IMAGE_DIR = HEXO_IMAGE_DIR + "/thumbs"
HEXO_POST_DIR = HEXO_SOURCE_DIR + '/_posts'

TEMPLATE_FILE = 'template.md'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y.%m.%d %H:%M:%S')


def get_hp_image_archive():
    try:
        response = requests.get(BING_IMAGE_URL, params=BING_PARAMS)
        response.raise_for_status()
        hp_image_archive = json.loads(response.text)
        if is_image_updated(hp_image_archive):
            download_image(hp_image_archive)
        else:
            time.sleep(3)
            get_hp_image_archive()
    except requests.exceptions.RequestException as ex:
        logging.exception(ex)
        time.sleep(3)
        get_hp_image_archive()


def is_image_updated(hp_image_archive):
    if hp_image_archive['images']:
        image = hp_image_archive['images'][0]
        image_date = image['enddate']
        return image_date == TODAY.strftime('%Y%m%d')
    else:
        return False


def download_image(hp_image_archive):
    image = hp_image_archive['images'][0]
    image_url = image['url'][1:]
    image_file_name = image_url.split('&')[0].replace('th?id=OHR.', '')
    try:
        response = requests.get(BING_URL + image_url, stream=True)
        response.raise_for_status()
        image_path = f'{HEXO_IMAGE_DIR}/{image_file_name}'
        with open(image_path, 'wb') as w:
            w.write(response.content)
        create_thumb(image_path, image_file_name)
        create_post(image, image_file_name)
        logging.info("crawler success.")
    except requests.exceptions.RequestException as ex:
        logging.exception(ex)
        time.sleep(3)
        download_image(hp_image_archive)


def create_thumb(image_path, image_file_name):
    raw_image = Image.open(image_path)
    raw_image.thumbnail((533, 300))
    thumb_file_name = image_file_name.replace('1920x1080', '533x300')
    raw_image.save(f'{HEXO_THUMB_IMAGE_DIR}/{thumb_file_name}')


def create_post(image, image_file_name):
    date = TODAY.strftime('%Y.%m.%d')
    title = image['copyright'].replace(': ', ' - ')

    template = open(TEMPLATE_FILE)
    lines = [Template(template.read()).substitute(date=date, title=title,
                                                  thumb_image=image_file_name.replace('1920x1080', '533x300'),
                                                  large_image=image_file_name,
                                                  image_name=image_file_name.split('_')[0])]

    post_title = TODAY.strftime('%Y-%m-%d.md')
    with open(f'{HEXO_POST_DIR}/{post_title}', 'w') as w:
        w.writelines(lines)


def generate_site():
    get_hp_image_archive()


if __name__ == '__main__':
    generate_site()
