#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/16 11:38
# @Author  : wjq
# @File    : html_clean.py
import json
import re
from copy import deepcopy
from urllib.parse import urljoin
from lxml import etree
from lxml.html import _transform_result, basestring, fromstring
from lxml.html.clean import Cleaner
from scrapy import Selector
from scrapy.conf import settings

from scrapy.selector import SelectorList

from en_p.utils.others import to_list

img_pattern = re.compile(r"""<img.*?src=[',"](.*?)[\',"].*?>""")
img_prefix = settings.get('IMG_PREFIX', 'http://43.250.238.143/pic/article/')


# img_fn = lambda x: x if x.startswith('http') or x.startswith(r'//') else urljoin(img_prefix, x)


def img_fn(x):
    if x.startswith('http'):
        return x
    elif x.startswith(r'//'):  # etl不能下载//开头的url图片
        return 'http:' + x
    else:
        return urljoin(img_prefix, x)


video_pattern = re.compile(r"""<video.*?src=[',"](.*?)[\',"].*?>""")
video_cover_pattern = re.compile(r"""poster=[',"](.*?)[\',"].*?>""")

# video_prefix = settings.get('VIDEO_PREFIX', 'http://43.250.238.143/video/article/')  # todo
# video_fn = lambda x: x if x.startswith('http') else urljoin(video_prefix, x)


re_tag = re.compile(r'<[^>]+>', re.S)  # todo why


def html2text(divs):
    return re_tag.sub('', divs).strip()


class Space(object):
    # 空格
    space_unicode = ['\u00A0', '\u0020', '\u3000']
    space_del = ['&nbsp;', '&ensp;', '&emsp;', '&thinsp;', '&zwnj;', '&zwj;']  # 删除
    space_res = ['\xa0']  # 保留
    """
    1.不间断空格\u00A0,主要用在office中,让一个单词在结尾处不会换行显示,快捷键ctrl+shift+space ;
    2.半角空格(英文符号)\u0020,代码中常用的;
    3.全角空格(中文符号)\u3000,中文文章中使用;
    """


class Interpunction(object):
    # 标点符号
    pass
    """
    符号 中文 英文
    句号 。 ,
    逗号 ， .
    顿号 、 \
    分号 ； ;
    冒号 ： :
    问号 ？ ?
    感叹号 ！ !
    引号 “” ""
    括号 （） ()
    省略号 …… …
    连接号 —— -
    书名号 《》 斜体
    """


class MyCleaner(Cleaner):
    del_attrs = [
        "style",  # 可有可无 Cleaner默认删除了style属性
        "href",
        "id",
        "name",
        "class",
        "width",
        "max-width",
        "min-width",
        "height",
        "max-height",
        "min-height",
        "top",
        "bottom",
        "right",
        "left",
        "align",
        "valign",
        "text-align, margin",
        "margin-left",
        "margin-right",
        "margin-top",
        "margin-bottom",
        "padding",
        "padding-top",
        "padding-right",
        "padding-left",
        "padding-bottom",
    ]
    
    # 标签保留
    whitelist_tags = set(["div", "p", "strong", "table", "th", "tr", "td", "thead", "tbody", "tfoot"])
    # A list of tags to include (default include all).
    remove_tags = set(['i', 'u', 'font', 's', 'em', 'hr', 'center', 'small', 'strike', 'a'])
    # A list of tags to kill.  Killing also removes the tag's content,i.e. the whole subtree, not just the tag itself.
    kill_tags = set(["iframe", "script", "button", "input", "style"])
    trans_tag_map = {'figure': 'div', 'figcaption': 'div'}
    kill_xpaths = [r'//*[contains(@style,"display:none")]', r'//*[text()="相关阅读："]/following::*', r'//*[text()="相关阅读："]',
                   r'//*[text()="相关链接："]/following::*', r'//*[text()="相关链接："]', r'//*[text()="相关新闻"]/following::*',
                   '//*[text()="相关新闻"]']
    safe_attrs = set(Cleaner.safe_attrs)  # 新浪客户端保留data-src
    safe_attrs.add('data-src')
    safe_attrs.add('data-original')
    
    def __init__(self, **kw):
        super(MyCleaner, self).__init__(**kw)
    
    def __call__(self, doc):
        super(MyCleaner, self).__call__(doc)
        for k, v in self.trans_tag_map.items():
            for el in doc.iter(k):
                el.tag = v
        del_attrs = set(self.del_attrs)
        for el in doc.iter(etree.Element):
            attrib = el.attrib
            for aname in attrib.keys():
                if aname in del_attrs:
                    del attrib[aname]  # todo 什么原理？改变了doc
    
    def clean_html(self, html, kill_xpaths=None):
        # if not kill_xpaths:
        #     return super(MyCleaner, self).clean_html(html)
        kill_xpaths = to_list(kill_xpaths) + to_list(self.kill_xpaths)
        
        if isinstance(html, basestring):
            doc = fromstring(html)  # 'HtmlElement' object
        else:
            doc = deepcopy(html)
        
        ele = []
        for i in kill_xpaths:
            try:
                ekill = doc.xpath(i)
            except Exception as e:
                print('没有找到kill_xpath: %s, 报错: %s' % (i, e))
                continue
            ele.extend(ekill)
        
        for e in ele:
            try:
                e.getparent().remove(e)
            except AttributeError as er:  # 防止包含重复删除 'NoneType' object has no attribute 'remove'
                print('tag: %s, attr: %s 的节点: 已被删除' % (e.tag, e.attrib))
        
        result_type = type(html)
        self(doc)
        return _transform_result(result_type, doc)


class Image(object):
    Extensions = ['BMP', 'jpg', 'JPG', 'JPEG', 'png', 'PNG', 'gif', 'GIF']
    Patterns = [r'<img.*?src=[\',"](.*?)[\',"].*?>', ]
    Repl = '${{%s}}$'


class NewsBaseParser(object):
    """新闻清洗类"""
    
    cleaner = MyCleaner()
    
    def image_clean(self, content):
        fr = re.finditer(img_pattern, content)
        media = {}
        new_content = ''
        
        for i, j in enumerate(fr):
            media.setdefault("images", {})
            st = content.find(j.group())
            end = st + len(j.group())
            new_content += content[:st] + '${{%s}}$' % (i + 1)
            content = content[end:]
            media['images'][str(i + 1)] = {"src": img_fn(j.group(1))}
        
        new_content += content
        new_content.replace('$$', '$<br>$')  # 连续2图片加换行
        return new_content, media
    
    def video_clean(self, content):
        fr = re.finditer(video_pattern, content)
        videos = {}
        cover = []
        
        new_content = ''
        
        for i, j in enumerate(fr):
            st = content.find(j.group())
            end = st + len(j.group())
            new_content += content[:st] + '#{{%s}}#' % (i + 1)
            content = content[end:]
            cover_img = video_cover_pattern.search(j.group())
            if cover_img:
                cover.append(
                    cover_img.group(1))  # todo check 1新闻多个视频， 有的视频有cover有的无cover， cover=[ imgurl, None, None,...]?
            
            videos[str(i + 1)] = {"src": j.group(1)}
        new_content += content
        return new_content, videos, cover
    
    def content_clean(self, content_div, need_video, kill_xpaths):
        c = self._myextract(content_div)
        c = self.cleaner.clean_html(c, kill_xpaths)  # 允许的类型：str
        cont_no_img, media = self.image_clean(c)  # 允许的类型：str
        # todo 把空行删除更彻底
        cont_no_img = cont_no_img.replace('<p><br></p>', '').replace('<div><br></div>', '').replace('\r\n', '').replace(
            '<div></div>', '').replace('<div>\n</div>', '').replace('<p><\p>', '').replace('</div>\n<div>',
                                                                                           '</div><div>')
        if not need_video:
            return cont_no_img, media, None, None
        else:
            cont_clean, videos, cover = self.video_clean(cont_no_img)
            return cont_clean, media, videos, cover
    
    def video_filter(self, sel_div):
        c = self._myextract(sel_div)
        if "video" in c or "flash" in c:
            return True  # 有视频要过滤
    
    def _myextract(self, select_div):
        """
        :param select_div:      Selector, SelectorList, str_list, or str
        :return:                str
        """
        # print('输入类型: %s' % type(select_div))
        
        if isinstance(select_div, (Selector, SelectorList)):  # SelectorList也是list, 所以首先判断SelectorList
            select_div = select_div.extract()  # 如果输入是Selector, 则此处得到str; 如果输入是SelectorList, 则此处得到str list
        if isinstance(select_div, list):
            c = ''.join(select_div)
        elif isinstance(select_div, str):
            c = select_div
        else:
            raise TypeError('select_div is not Selector, SelectorList, str_list or str, it is %s!' % type(select_div))
        return c
    
    def page_turn_filter(self, content_div):
        if content_div.xpath('.//div[contains(@class, "swiper")]'):  # 注意加.否则 网页其他部分包含"swiper"js也被错误过滤
            return True
        if '【1】' in content_div.extract():
            return True
        lasts = content_div.xpath('.//*[last()]')  # todo check fix_bug
        for i in lasts:
            page_turn_divs = i.xpath('.//*[re:test(text(),"(?:共\d+页|上一页|下一页|上1页|下1页|Prev|Next|\d+/\d+)")]')
            if page_turn_divs:
                return page_turn_divs  # 是分页要过滤


def json_load_html(html_str):
    html_str = html_str.replace('\r', '').replace('\n', '').replace('\t', '')
    html_str = re.sub('\'', '\"', html_str)
    html_str = re.sub("u'", "\"", html_str)
    return json.loads(html_str)


if __name__ == '__main__':
    s = """'<p>\u3000\u3000<a target="_blank" href="http://www.chinanews.com/">中新网</a>1月30日电 据俄罗斯卫星网报道，意大利人保罗·温图里尼在地球上最冷的居民点——雅库特(东西伯利亚)的奥伊米亚康，做了之前任何人都没能成功的事情。这名意大利警界代表在零下52度的严寒中，用3小时54分10秒跑完了39公里。</p><p>\u3000\u3000据报道，温图里尼说：“我很高兴我达到了最好的结果。暂时还不急着说这个结果已载入历史，虽然这样的事很少有人做，可能都没有人做。我的团队乘坐俄罗斯紧急情况部特殊的卡马斯车从雅库特到奥伊米亚康的旅行是一次真正的冒险。”</p><p>\u3000\u3000温图里尼称：“卡车电力系统的故障导致我们走到零下56度的严 寒中。整个团队都遇到了危险。但是俄罗斯紧急情况部的孩子们很快地了解情况，给我们送来了暖和的衣服，我们夜里徒步前往气象站寻求帮助。”</p><p>\u3000\u3000报道称，温图里尼表示，在这种极限天气中，没有特殊的跑步装备。他说：“我穿的衣服不多，因此很 容易感觉到冷。在跑到30公里时我的衣服成了冰壳，它差点影响我继续跑下去。”</p>'"""
    s = '''<div class="content_con">
            <p>【环球网报道 记者 朱梦颖】路透社刚刚消息：印度空军一架军机在印控克什米尔地区坠毁，两名飞行员和一名平民遇难。</p><p><img src="https://t1.huanqiu.cn/10c7a6fd51ce803903fad50a21895ce7.jpg" data-alt=""></p>
        </div>'''
    
    s = '''<div class="left_zw" style="position:relative">

<p>　　来源：中国侨网微信公众号 (ID:qiaowangzhongguo)作者：韩辉</p>

<div class="pictext xh-highlight" style="text-align:center;text-indent:2em; "></div>

<div style="text-align:center" class="xh-highlight"><img src="http://www.chinaqw.com/2019/0304/20193493255.gif" style="border:px solid #000000"></div><table border="0" cellspacing="0" cellpadding="0" align="left" style="padding-right:10px;" class="xh-highlight"><tbody><tr><td></td></tr></tbody></table><div id="function_code_page" class="xh-highlight"></div>

                </div>'''
    
    # kill_xpaths = '//p[contains(text(),"来源：中国侨网微信公众号")]/following-sibling::*'  # 所有兄弟
    #
    # s = '''<div class=\"u-mainText\">\r\n                    <!--enpproperty <articleid>32754452</articleid><date>2019-04-18 11:18:16.0</date><author></author><title>福建武夷山：谷雨将至采茶忙(1)_光明网</title><keyword>福建武夷山,茶场,采茶,芳华,谷雨</keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>5557</nodeid><nodename>综合新闻</nodename><nodesearchname></nodesearchname>/enpproperty--><!--enpcontent--><!--enpcontent--><p align=\"center\"><a href=\"content_32754452_2.htm\" target=\"_self\"><img id=\"67746815\" border=\"0\" alt=\"#（社会）（1）福建武夷山：谷雨将至采茶忙\" src=\"http://imgtech.gmw.cn/attachement/jpg/site2/20190418/94c69122e4b71e2231e11c.jpg\" title=\"福建武夷山：谷雨将至采茶忙\"></a></p>\n<p class=\"pictext\" align=\"center\">　　4月17日，在福建省武夷山佛国岩芳华茶场，茶农在采摘岩茶青叶。</p>\n<p>　　谷雨临近，茶乡福建武夷山进入一年中繁忙的制茶季。今年，福建武夷山气候温和，茶园里茶芽长势喜人。</p>\n<p>　　新华社发（陈颖 摄）</p>\n<!--/enpcontent--><div width=\"100%\" id=\"displaypagenum\"><p></p><center> <span>1</span> <a href=\"content_32754452_2.htm\">2</a> <a href=\"content_32754452_3.htm\">3</a> <a href=\"content_32754452_4.htm\">4</a> <a href=\"content_32754452_5.htm\">5</a> <a href=\"content_32754452_2.htm\">下一页</a> <span></span></center></div><div id=\"mpagecount\" style=\"display:none\">5</div><div id=\"mcurrentpage\" style=\"display:none\">1</div><!--/enpcontent-->\r\n\t\t\t\t\t\r\n                    <!--责编-->\r\n                    <div class=\"m-zbTool liability\">\r\n                    \t<span>[ </span><span class=\"liability\">责编：张佳兴</span><span> ]</span>                    \r\n                   </div>\r\n                    \r\n                </div><div class=\"u-mainText\">\r\n                    <!--enpproperty <articleid>32754452</articleid><date>2019-04-18 11:18:16.0</date><author></author><title>福建武夷山：谷雨将至采茶忙(2)_光明网</title><keyword>福建武夷山,茶场,采茶,芳华,谷雨</keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>5557</nodeid><nodename>综合新闻</nodename><nodesearchname></nodesearchname>/enpproperty--><!--enpcontent--><!--enpcontent-->\n\n<p align=\"center\"><a href=\"content_32754452_3.htm\" target=\"_self\"><img id=\"67746816\" border=\"0\" alt=\"#（社会）（2）福建武夷山：谷雨将至采茶忙\" src=\"http://imgtech.gmw.cn/attachement/jpg/site2/20190418/94c69122e4b71e2231e11d.jpg\" title=\"福建武夷山：谷雨将至采茶忙\"></a></p>\n<p class=\"pictext\">　　4月17日，在福建省武夷山佛国岩芳华茶场，茶农将采摘的岩茶青叶装筐集中。</p>\n<p>　　新华社发（陈颖 摄）</p>\n<!--/enpcontent--><div width=\"100%\" id=\"displaypagenum\"><p></p><center> <span></span> <a href=\"content_32754452.htm\">上一页</a> <a href=\"content_32754452.htm\">1</a> <span>2</span> <a href=\"content_32754452_3.htm\">3</a> <a href=\"content_32754452_4.htm\">4</a> <a href=\"content_32754452_5.htm\">5</a> <a href=\"content_32754452_3.htm\">下一页</a> <span></span></center></div><div id=\"mpagecount\" style=\"display:none\">5</div><div id=\"mcurrentpage\" style=\"display:none\">2</div><!--/enpcontent-->\r\n\t\t\t\t\t\r\n                    <!--责编-->\r\n                    <div class=\"m-zbTool liability\">\r\n                    \t<span>[ </span><span class=\"liability\">责编：张佳兴</span><span> ]</span>                    \r\n                   </div>\r\n                    \r\n                </div><div class=\"u-mainText\">\r\n                    <!--enpproperty <articleid>32754452</articleid><date>2019-04-18 11:18:16.0</date><author></author><title>福建武夷山：谷雨将至采茶忙(3)_光明网</title><keyword>福建武夷山,茶场,采茶,芳华,谷雨</keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>5557</nodeid><nodename>综合新闻</nodename><nodesearchname></nodesearchname>/enpproperty--><!--enpcontent--><!--enpcontent-->\n\n<p align=\"center\"><a href=\"content_32754452_4.htm\" target=\"_self\"><img id=\"67746817\" border=\"0\" alt=\"#（社会）（3）福建武夷山：谷雨将至采茶忙\" src=\"http://imgtech.gmw.cn/attachement/jpg/site2/20190418/94c69122e4b71e2231e11e.jpg\" title=\"福建武夷山：谷雨将至采茶忙\"></a></p>\n<p class=\"pictext\" align=\"center\">　　4月17日，在福建省武夷山佛国岩芳华茶场，茶农在采摘岩茶青叶。</p>\n<p>　　新华社发（陈颖 摄）</p>\n<!--/enpcontent--><div width=\"100%\" id=\"displaypagenum\"><p></p><center> <span></span> <a href=\"content_32754452_2.htm\">上一页</a> <a href=\"content_32754452.htm\">1</a> <a href=\"content_32754452_2.htm\">2</a> <span>3</span> <a href=\"content_32754452_4.htm\">4</a> <a href=\"content_32754452_5.htm\">5</a> <a href=\"content_32754452_4.htm\">下一页</a> <span></span></center></div><div id=\"mpagecount\" style=\"display:none\">5</div><div id=\"mcurrentpage\" style=\"display:none\">3</div><!--/enpcontent-->\r\n\t\t\t\t\t\r\n                    <!--责编-->\r\n                    <div class=\"m-zbTool liability\">\r\n                    \t<span>[ </span><span class=\"liability\">责编：张佳兴</span><span> ]</span>                    \r\n                   </div>\r\n                    \r\n                </div><div class=\"u-mainText\">\r\n                    <!--enpproperty <articleid>32754452</articleid><date>2019-04-18 11:18:16.0</date><author></author><title>福建武夷山：谷雨将至采茶忙(4)_光明网</title><keyword>福建武夷山,茶场,采茶,芳华,谷雨</keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>5557</nodeid><nodename>综合新闻</nodename><nodesearchname></nodesearchname>/enpproperty--><!--enpcontent--><!--enpcontent-->\n\n<p align=\"center\"><a href=\"content_32754452_5.htm\" target=\"_self\"><img id=\"67746818\" border=\"0\" alt=\"#（社会）（4）福建武夷山：谷雨将至采茶忙\" src=\"http://imgtech.gmw.cn/attachement/jpg/site2/20190418/94c69122e4b71e2231e11f.jpg\" title=\"福建武夷山：谷雨将至采茶忙\"></a></p>\n<p class=\"pictext\">　　4月17日，在福建省武夷山佛国岩芳华茶场，茶农进入茶场准备采茶。</p>\n<p>　　新华社发（陈颖 摄）</p>\n<!--/enpcontent--><div width=\"100%\" id=\"displaypagenum\"><p></p><center> <span></span> <a href=\"content_32754452_3.htm\">上一页</a> <a href=\"content_32754452.htm\">1</a> <a href=\"content_32754452_2.htm\">2</a> <a href=\"content_32754452_3.htm\">3</a> <span>4</span> <a href=\"content_32754452_5.htm\">5</a> <a href=\"content_32754452_5.htm\">下一页</a> <span></span></center></div><div id=\"mpagecount\" style=\"display:none\">5</div><div id=\"mcurrentpage\" style=\"display:none\">4</div><!--/enpcontent-->\r\n\t\t\t\t\t\r\n                    <!--责编-->\r\n                    <div class=\"m-zbTool liability\">\r\n                    \t<span>[ </span><span class=\"liability\">责编：张佳兴</span><span> ]</span>                    \r\n                   </div>\r\n                    \r\n                </div><div class=\"u-mainText\">\r\n                    <!--enpproperty <articleid>32754452</articleid><date>2019-04-18 11:18:16.0</date><author></author><title>福建武夷山：谷雨将至采茶忙(5)_光明网</title><keyword>福建武夷山,茶场,采茶,芳华,谷雨</keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>5557</nodeid><nodename>综合新闻</nodename><nodesearchname></nodesearchname>/enpproperty--><!--enpcontent--><!--enpcontent-->\n\n<p align=\"center\"><img id=\"67746819\" alt=\"#（社会）（5）福建武夷山：谷雨将至采茶忙\" src=\"http://imgtech.gmw.cn/attachement/jpg/site2/20190418/94c69122e4b71e2231e120.jpg\" title=\"福建武夷山：谷雨将至采茶忙\"></p>\n<p>　　4月17日，在福建省武夷山佛国岩芳华茶场，制茶师潘行彪（中）在处理刚采摘下来的岩茶青叶。</p>\n<p>　　新华社发（陈颖 摄）<a href=\"http://www.gmw.cn\"><img src=\"https://img.gmw.cn/pic/content_logo.png\" title=\"返回光明网首页\"></a></p><!--/enpcontent--><div width=\"100%\" id=\"displaypagenum\"><p></p><center> <span></span> <a href=\"content_32754452_4.htm\">上一页</a> <a href=\"content_32754452.htm\">1</a> <a href=\"content_32754452_2.htm\">2</a> <a href=\"content_32754452_3.htm\">3</a> <a href=\"content_32754452_4.htm\">4</a> <span>5</span></center></div><div id=\"mpagecount\" style=\"display:none\">5</div><div id=\"mcurrentpage\" style=\"display:none\">5</div><!--/enpcontent-->\r\n\t\t\t\t\t\r\n                    <!--责编-->\r\n                    <div class=\"m-zbTool liability\">\r\n                    \t<span>[ </span><span class=\"liability\">责编：张佳兴</span><span> ]</span>                    \r\n                   </div>\r\n                    \r\n                </div>'''
    # kill_xpaths = [r'//img[@src="https://img.gmw.cn/pic/content_logo.png"]',
    #                                           r'//div[@class="pageNum"]',
    #                                           r'//div[@id="displaypagenum"]',
    #                r'//div[@class="m-zbTool liability"]'
    #                                           ]
    # cleaner = MyCleaner()
    # cc = cleaner.clean_html(s, kill_xpaths)
    # print(type(cc))
    # print(cc)
    
    s = '''<a href="JavaScript:void(0)">
<img src="//dataimage/png" data-src="https://n.sinaimg.cn/default.jpg" alt="">
<img src="data:image/png" data-src="https://n.sinaimg.cn/default.jpg" alt="">
</a>
'''
    cleaner = MyCleaner()
    cc = cleaner.clean_html(s, kill_xpaths=['//*[@class="art_tit_h1"]', '//*[@class="art_time"]', '//div[@id="wx_pic"]',
                                            '//img[@class="sharePic hide"]'])
    print(cc)
