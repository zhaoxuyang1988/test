#-*- coding:utf-8 -*-
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


if __name__ == "__main__":
    c = CrawlerProcess(get_project_settings())
    #c.crawl("daly")
    #c.crawl("globaltimes")
    c.crawl("cnn")
    c.start()