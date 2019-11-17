# -*- coding:utf-8 -*-

import json
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from en_p.utils.html_clean import NewsBaseParser
from newspaper import Article
from en_p.items import EnPItem
from en_p.utils.files import save_mess



class EnPeople(CrawlSpider):
    name = "sina"

    allowed_domains = ['english.sina.com']
    start_urls = [
        "http://english.sina.com/index.html"]

    rules = (
     Rule(LinkExtractor(allow=(r'http://english.sina.com/.*?.shtml',)), follow=True, callback='parse_item'),

    )

    def parse_item(self, response):

        tags = []
        tag = response.xpath('//*[@class="tag"]/a/text()').extract()
        tags.append(tag)
        tag = response.xpath('//*[@class="tag_cont"]/a/text()').extract()
        tags.append(tag)

        item = EnPItem()
        art_parser = Article(response.url, language='en', fetch_images=False)
        # a.download()
        art_parser.set_html(response.text)
        art_parser.parse()

        item["home"] = response.url
        item["title"] = art_parser.title

        item["content"] = art_parser.text
        item["authors"] = art_parser.authors
        try:
            item["publish_date"] = art_parser.publish_date.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        item["images"] = list(art_parser.images)
        item["keywords"] = art_parser.keywords
        item["meta_keywords"] = art_parser.meta_keywords
        item["tags"] = tags #list(art_parser.tags)

        save_mess("%s.txt"%self.name, json.dumps(dict(item), ensure_ascii=False))

