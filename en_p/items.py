# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class EnPItem(scrapy.Item):
    # define the fields for your item here like:
    home = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    authors = scrapy.Field()
    publish_date = scrapy.Field()
    images = scrapy.Field()
    keywords = scrapy.Field()
    meta_keywords = scrapy.Field()
    tags = scrapy.Field()
        
    