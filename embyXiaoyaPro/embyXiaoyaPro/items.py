# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EmbyxiaoyaproItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    urls = scrapy.Field()
    filename = scrapy.Field()
    filesize = scrapy.Field()


class XiaoyaStrmItem(scrapy.Item):
    # path = scrapy.Field()
    content = scrapy.Field()
    pathCache = scrapy.Field()
