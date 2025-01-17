import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from string import Template

import PIL.Image
import requests
from requests import HTTPError
from retry import retry

from models import *

BING_API_URL = 'https://cn.bing.com/hp/api/model'
BING_API_PARAMS = {'mkt': 'zh-CN'}
BING_API_HEADERS = {'accept-language': 'zh-CN,zh;'}

TZ_SHANGHAI = timezone(timedelta(hours=8), name='Asia/Shanghai')
TODAY = datetime.now(TZ_SHANGHAI)

HEXO_SOURCE_DIR = Path('source')
HEXO_IMAGE_DIR = HEXO_SOURCE_DIR / 'images'
HEXO_THUMB_IMAGE_DIR = HEXO_IMAGE_DIR / 'thumbs'
HEXO_POST_DIR = HEXO_SOURCE_DIR / '_posts'

TEMPLATE_FILE = 'template.md'


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )


@retry(tries=3, delay=3, backoff=2)
def get_image():
    try:
        response = requests.get(BING_API_URL, params=BING_API_PARAMS, headers=BING_API_HEADERS)
        response.raise_for_status()
        logging.info(response.text)
        api_model = ApiModel.from_dict(response.json())
        for media_content in api_model.media_contents:
            if datetime.strptime(media_content.full_date_string, '%Y %m月 %d').date() == TODAY.date():
                return media_content.image_content
    except HTTPError as e:
        logging.exception('get daily wallpaper failed.')
        raise e


@retry(tries=3, delay=3, backoff=2)
def download_image(image_content):
    image = image_content.image
    image_url = get_image_url(image)
    image_file_name = get_image_file_name(image_url)
    logging.info('url: %s, filename: %s', image_url, image_file_name)
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image_path = HEXO_IMAGE_DIR / image_file_name
        with open(image_path, 'wb') as w:
            w.write(response.content)
        return image_file_name
    except Exception as e:
        logging.exception('image download failed')
        raise e


def get_image_url(image):
    image_url = image.url.replace('webp', 'jpg')
    if not image_url.startswith('https://'):
        if image_url.startswith('/'):
            image_url = image_url[1:]
        image_url = 'https://s.cn.bing.net/' + image_url
    return image_url


def get_image_file_name(image_url):
    return image_url.split('&')[0].split('=')[1].replace('OHR.', '')


def create_thumb(image_file_name):
    try:
        with PIL.Image.open(HEXO_IMAGE_DIR / image_file_name) as raw:
            raw.thumbnail((533, 300))
            thumb_file_name = image_file_name.replace('1920x1080', '533x300')
            raw.save(HEXO_THUMB_IMAGE_DIR / thumb_file_name)
    except Exception as e:
        logging.exception('create thumb image failed')
        raise e


def create_post(image_content, image_file_name):
    date = TODAY.strftime('%Y.%m.%d')
    title = f"{image_content.title} ({image_content.copyright.replace(': ', ' - ')})"
    thumb_image=image_file_name.replace('1920x1080', '533x300')
    image_name=image_file_name.split('_')[0]

    try:
        with open(TEMPLATE_FILE) as template_file:
            lines = [Template(template_file.read()).substitute(date=date, title=title, thumb_image=thumb_image,
                                                          large_image=image_file_name, image_name=image_name)]

            post_title = TODAY.strftime('%Y-%m-%d.md')
            with open(f'{HEXO_POST_DIR}/{post_title}', 'w', encoding='utf-8') as w:
                w.writelines(lines)
    except Exception as e:
        logging.exception('create post failed')
        raise e


if __name__ == '__main__':
    setup_logging()
    image_content = get_image()
    image_file_name = download_image(image_content)
    create_thumb(image_file_name)
    create_post(image_content, image_file_name)
