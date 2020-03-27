# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime


def strip_lines(lines: list):
    return [' '.join(text.split()) for text in lines]


def strip_line(text: str):
    return ''.join(text.split())


class HabrBlogSpider(scrapy.Spider):
    name = 'habr_blog'
    allowed_domains = ['habr.com']
    start_urls = ['https://habr.com/ru/top/weekly']

    def parse(self, response):
        pagination_urls = response.css('ul#nav-pagess li a::attr("href")').extract()

        for itm in pagination_urls:
            yield response.follow(itm, callback=self.parse)

        for post_url in response.css('ul.content-list_posts li a.post__title_link::attr("href")'):
            yield response.follow(post_url, callback=self.post_parse)

    def post_parse(self, response):
        post_meta = response.xpath("//header[contains(@class, 'post__meta')]")
        author_selector = post_meta.xpath("//a[contains(@class, 'post__user-info')]")

        # with css and little xpath
        data = {
            'title': response.css('span.post__title-text::text').extract_first(),
            'url': response.url,
            'author': author_selector.css('span.user-info__nickname::text').extract_first(),
            'author_url': author_selector.css('::attr(href)').extract_first(),
            'publish_time': post_meta.css("span.post__time::attr(data-time_published)").extract_first(),
            'tags': strip_lines(response.xpath("//dt[contains(text(), 'Теги')]/..").css("a.post__tag::text").extract()),
            'hubs': strip_lines(response.xpath("//dt[contains(text(), 'Хабы')]/..").css("a.post__tag::text").extract()),
            'comments_count': strip_line(response.css("span#comments_count::text").extract_first()),
            'parse_time': datetime.now()
        }

        # with xpath
        # data = {
        #     'url': response.url,
        #
        #     'title': post_meta.xpath(
        #         "//span[contains(@class, 'post__title-text')]/text()").extract_first(),
        #
        #     'author': author_selector.xpath(
        #         "//span[contains(@class, 'user-info__nickname')]/text()").extract_first(),
        #
        #     'author_url': author_selector.xpath('@href').extract_first(),
        #
        #     'publish_time': post_meta.xpath(
        #         "//span[contains(@class, 'post__time')]/@data-time_published").extract_first(),
        #
        #     'tags': strip_lines(response.xpath(
        #         "//dt[contains(text(), 'Теги')]/..//a[contains(@class, 'post__tag')]/text()").extract()),
        #
        #     'hubs': strip_lines(response.xpath(
        #         "//dt[contains(text(), 'Хабы')]/..//a[contains(@class, 'post__tag')]/text()").extract()),
        #
        #     'comments_count': strip_line(response.xpath(
        #         "//span[@id='comments_count']/text()").extract_first()),
        #
        #     'parse_time': datetime.now()
        # }
        yield data
