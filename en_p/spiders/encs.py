# -*- coding:utf-8 -*-

import json
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from en_p.utils.html_clean import NewsBaseParser
from newspaper import Article
from en_p.items import EnPItem
from en_p.utils.files import save_mess



class EnPeople(CrawlSpider):
    name = "encs"

    allowed_domains = ['www.ecns.cn']
    start_urls = [
        "http://www.ecns.cn/"]

    rules = (

        # Rule(LinkExtractor(allow=(r'http://en.people.cn/n3/2019/1106/c90000-9629741.html', )),follow=True, callback='parse_item'),
        #Rule(LinkExtractor(allow=(r'http://en.people.cn/.*?.html',)), follow=True, callback='parse_item'),
        Rule(LinkExtractor(allow=(r'http://www.ecns.cn/.*?.shtml',)), follow=True, callback='parse_item'),
    )

    def parse_item(self, response):

        tag = response.url.split("/")[3]


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
        item["tags"] = tag #list(art_parser.tags)

        print(item)
        save_mess("%s.txt"%self.name, json.dumps(dict(item), ensure_ascii=False))

