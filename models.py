from dataclasses import dataclass
from typing import Any
from typing import List


@dataclass
class Image:
    url: str
    wallpaper: str
    downloadable: bool

    @staticmethod
    def from_dict(obj: Any) -> 'Image':
        _url = str(obj.get('Url'))
        _wallpaper = str(obj.get('Wallpaper'))
        _downloadable = bool(obj.get('Downloadable'))
        return Image(_url, _wallpaper, _downloadable)


@dataclass
class ImageContent:
    description: str
    image: Image
    headline: str
    title: str
    copyright: str
    trivia_id: str

    @staticmethod
    def from_dict(obj: Any) -> 'ImageContent':
        _description = str(obj.get('Description'))
        _image = Image.from_dict(obj.get('Image'))
        _headline = str(obj.get('Headline'))
        _title = str(obj.get('Title'))
        _copyright = str(obj.get('Copyright'))
        _trivia_id = str(obj.get('TriviaId'))
        return ImageContent(_description, _image, _headline, _title, _copyright, _trivia_id)


@dataclass
class MediaContent:
    image_content: ImageContent
    ssd: str
    full_date_string: str

    @staticmethod
    def from_dict(obj: Any) -> 'MediaContent':
        _image_content = ImageContent.from_dict(obj.get('ImageContent'))
        _ssd = str(obj.get('Ssd'))
        _full_date_string = str(obj.get('FullDateString'))
        return MediaContent(_image_content, _ssd, _full_date_string)


@dataclass
class ApiModel:
    media_contents: List[MediaContent]

    @staticmethod
    def from_dict(obj: Any) -> 'ApiModel':
        _media_contents = [MediaContent.from_dict(c) for c in obj.get('MediaContents')]
        return ApiModel(_media_contents)
