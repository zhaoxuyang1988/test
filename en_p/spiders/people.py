#-*- coding:utf-8 -*-

import json
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from en_p.utils.html_clean import NewsBaseParser
# from newspaper import Article
from en_p.items import EnPItem
from en_p.utils.files import save_mess, get_int_list
from en_p.utils.time_translater import get_datetime_ago
from scrapy.http import Request
# from newspaper.configuration import Configuration

class pCrawlSpider(CrawlSpider):

    def _build_request(self, rule, link):
        r = Request(url=link.url, 
                    callback=self._response_downloaded,
                    priority=1)
        r.meta.update(rule=rule, link_text=link.text)
        return r
    
class EnPeople(pCrawlSpider):
    
    
    name = "people"

    
    allowed_domains = ['en.people.cn']
    start_urls = ["http://en.people.cn/review/%s.html"%"".join(get_int_list(get_datetime_ago(days=idx).strftime('%Y-%m-%d'))) 
                  for idx in range(3662, -1, -1)]

    rules = (
        
        #Rule(LinkExtractor(allow=(r'http://en.people.cn/n3/2019/1106/c90000-9629741.html', )),follow=True, callback='parse_item'),
        Rule(LinkExtractor(allow=(r'http://en.people.cn/.*?.html', )),follow=True, callback='parse_item'),
    )

    def parse_item(self, response):
        pass
        # item = EnPItem()
        # art_parser = Article(response.url, language='en', fetch_images=False)
        # #a.download()
        # art_parser.set_html(response.text)
        # art_parser.parse()
        #
        # item["home"] = response.url
        # item["title"] = art_parser.title
        #
        # item["content"] = art_parser.text
        # item["authors"] = art_parser.authors
        # try:
        #     item["publish_date"] = art_parser.publish_date.strftime('%Y-%m-%d %H:%M:%S')
        # except:
        #     pass
        # item["images"] = list(art_parser.images)
        # item["keywords"] = art_parser.keywords
        # item["meta_keywords"] = art_parser.meta_keywords
        # item["tags"] = list(art_parser.tags)
        #
        # save_mess("en_people.txt", json.dumps(dict(item), ensure_ascii=False))
        
