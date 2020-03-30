# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst


def clean_photo(values):
    if values[:2] == '//':
        return f'https:{values}'
    return values


def strip_first_str_el(lines: list):
    return ' '.join(lines[0].split())


def hook_user_url(url: list):
    return f'https://www.avito.ru{url[0]}'


class AvitoRealEstateItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(output_processor=TakeFirst())
    photos = scrapy.Field(input_processor=MapCompose(clean_photo))
    published_date = scrapy.Field(output_processor=strip_first_str_el)
    parsed_date = scrapy.Field(output_processor=TakeFirst())
    author_name = scrapy.Field(output_processor=strip_first_str_el)
    author_url = scrapy.Field(output_processor=hook_user_url)
    params = scrapy.Field(output_processor=TakeFirst())
    phone = scrapy.Field(output_processor=TakeFirst())
