#-*- coding:utf-8 -*-


from scrapy.spiders import Spider
from scrapy import Request
from utils.files import get_content_list
from newspaper import Article
from en_p.items import EnPItem
from en_p.utils.files import save_mess

API_URL = "https://www.sciencedaily.com/xml/summaries.php?"\
                "section={}&topic={}&&start={}&end={}"


class sciSpider(Spider):

    name = "science"

    def start_requests(self):
        for line in get_content_list("science.txt"):
            values = line.split("/")
            if len(values) != 3:
                continue
            cur_page = 1
            url = API_URL.format(values[0], values[1], (cur_page-1)*20, cur_page*20)

            meta_data = {"page":cur_page,
                         "tags":[values[0], values[1]]}

            yield Request(url, meta=meta_data)

    def parse(self, response):
        page_idx = response.meta["page"]
        tags = response.meta["tags"]

        links = response.xpath('//*[@class="latest-head"]/a/@href').extract()
        for link in links:
            yield Request("https://www.sciencedaily.com%s"%link,
                          callback=self.parse_article,
                          meta={"tags":tags})

        url = API_URL.format(tags[0], tags[1], (page_idx) * 20, (page_idx+1) * 20)
        meta_data = {"page": page_idx+1,
                     "tags": [tags[0], tags[1]]}

        yield Request(url, meta=meta_data)


    def parse_article(self, response):

        tags = response.meta["tags"]
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
        item["tags"] = tags  # list(art_parser.tags)

        print(item)
        save_mess("%s.txt" % self.name, json.dumps(dict(item), ensure_ascii=False))