from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from blogparse import settings
from blogparse.spiders.habr_blog import HabrBlogSpider
from blogparse.spiders.avito import AvitoSpider


if __name__ == '__main__':
    craw_settings = Settings()

    # for debug mode
    settings.AUTOTHROTTLE_ENABLED = True
    settings.LOG_ENABLED = True

    craw_settings.setmodule(settings)
    crawler_proc = CrawlerProcess(settings=craw_settings)
    # crawler_proc.crawl(HabrBlogSpider)
    crawler_proc.crawl(AvitoSpider)
    crawler_proc.start()
