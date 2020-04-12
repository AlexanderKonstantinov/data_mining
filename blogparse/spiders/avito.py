# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from blogparse.items import AvitoRealEstateItem
from datetime import datetime


class AvitoSpider(scrapy.Spider):
    name = 'avito'
    allowed_domains = ['www.avito.ru', 'avito.ru', 'm.avito.ru' ]
    start_urls = ['https://www.avito.ru/habarovsk/kvartiry']

    def parse(self, response):
        pages_num = response.xpath("//span[@data-marker='pagination-button/next']/preceding-sibling::span[1]/text()").get()

        if pages_num is None:
            return

        pages_num = int(pages_num)
        base_url = response.url

        for page_num in range(1, pages_num + 1):
            yield response.follow(f'{base_url}?p={page_num}', callback=self.parse_page)

    def parse_page(self, response):
        ads_urls = response.css("div.item_table h3.snippet-title a.snippet-link::attr('href')")

        for url in ads_urls:
            yield response.follow(url, callback=self.ads_parse)

    def ads_parse(self, response):
        item = ItemLoader(AvitoRealEstateItem(), response)
        item.add_value('url', response.url)
        item.add_css('title', 'div.title-info-main h1.title-info-title span::text')
        item.add_xpath('photos', "//div[contains(@class, 'gallery-img-frame')]/@data-url")
        item.add_css('published_date', 'div.title-info div.title-info-metadata-item-redesign::text')
        item.add_value('parsed_date', datetime.now())
        item.add_css('author_name', 'div.item-view-info div.seller-info-name a::text')
        item.add_css('author_url', "div.item-view-info div.seller-info-name a::attr('href')")

        params = {}
        for param_selector in response.css('div.item-view-block ul.item-params-list li'):
            param = param_selector.css('::text')
            params[param[1].get()] = param[2].get()

        item.add_value('params', params)
        yield item.load_item()

