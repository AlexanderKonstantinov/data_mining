# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from blogparse.items import ZillowItem
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time


class ZillowSpider(scrapy.Spider):
    name = 'zillow'
    allowed_domains = ['www.zillow.com']
    start_urls = ['https://www.zillow.com/tx/']
    # browser = webdriver.Chrome('C:\\webdrivers\\chromedriver.exe')
    browser = webdriver.Firefox(executable_path=r'C:\webdrivers\geckodriver.exe')

    def parse(self, response):

        for pag_url in response.xpath("//nav[@aria-label='Pagination']/ul/li/a/@href"):
            yield response.follow(pag_url, callback=self.parse)

        for ads_url in response.xpath("//ul[contains(@class, 'photo-cards_short')]/li/article//a/@href"):
            yield response.follow(ads_url, callback=self.ads_parse)

    def ads_parse(self, response):
        item = ItemLoader(ZillowItem(), response)
        self.browser.get(response.url)
        media_col = self.browser.find_element_by_css_selector('.ds-media-col')

        get_photos = lambda: self.browser.find_elements_by_xpath(
            "//ul[@class='media-stream']/li/picture/source[@type='image/jpeg']")

        photos_count_current = len(get_photos())

        while True:
            media_col.send_keys(Keys.PAGE_DOWN)
            media_col.send_keys(Keys.PAGE_DOWN)
            media_col.send_keys(Keys.PAGE_DOWN)
            media_col.send_keys(Keys.PAGE_DOWN)
            media_col.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)
            photos_count_after = len(get_photos())

            if photos_count_current == photos_count_after:
                break

            photos_count_current = photos_count_after

        images = {itm.get_attribute('srcset').split(' ')[-2] for itm in get_photos()}

        item.add_css('address', 'div#ds-data-view div.ds-home-details-chip h1 span::text')
        item.add_css('price', 'div#ds-data-view div.ds-home-details-chip h3.ds-price span::text')
        area = ''.join(response
                       .css('div#ds-data-view div.ds-home-details-chip')
                       .xpath("//header/h3/span[@class='ds-bed-bath-living-area']")[-1]
                       .css('span::text').extract())
        item.add_value('area', area)
        item.add_value('url', response.url)
        item.add_value('photos', images)

        yield item.load_item()
