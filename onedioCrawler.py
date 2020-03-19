import requests
from bs4 import BeautifulSoup
import json
import re

class Source():
    def __init__(self, name, domain, favicon):
        self.name = name
        self.domain = domain
        self.favicon = favicon
    def jason_creater(self):
        d = dict()
        d['name'] = self.name
        d['domain'] = self.domain
        d['favicon'] = self.favicon
        return d

class Content():
    def __init__(self, url, title, publish_date, content, source):
        self.url = url
        self.title = title
        self.publish_date = publish_date
        self.content = content
        self.source = source

    def jason_creater(self):
        d = dict()
        d['url'] = self.url
        d['title'] = self.title
        d['date'] = self.publish_date
        d['content'] = self.content
        d['source'] = self.source.jason_creater()
        return d

class OnedioCrawler:

    domain = "https://onedio.com" #source domain is default. not searching at all
    baseUrl = "https://onedio.com/ara/haber/"
    favicon = "https://onedio.com/favicons/favicon-160x160.png"

    def domain_handler(self, keyword, date=None, pageNumber = 1):
        dates = {'day', 'week', 'month', 'year'}
        keyword = keyword.replace(' ', '%20')
        if (date in dates):
            return "{}{}?date={}&page={}".format(self.baseUrl, keyword, date, pageNumber)
        return "{}{}?page={}".format(self.baseUrl, keyword, pageNumber)

    def get_beautiful_html(self, url):
        try:
            req = requests.get(url)
        except requests.exceptions.RequestException as e:
            print('Exception accured {}'.format(e))
        return BeautifulSoup(req.text, 'html.parser')

    def search_href(self, bs):
        pages = set()
        resultSection = bs.select_one('div.search-results')
        urlSoup = resultSection.find_all('a', href=True)
        for result in urlSoup:
            if result['href'] not in pages:
                pages.add("https://onedio.com{}".format(result['href']))
        return pages

    # scrapes user link and title
    def get_header(self, bs):
        main_article = bs.select_one('.main')
        if (main_article == None):
            print('could not find main article section')
        try:
            header = main_article.select_one('header')  # main > article > header
        except:
            header = "0"
        try:
            title = header.find('h1').get_text()
        except:
            title = "0"
        try:
            user = header.select_one(".user").select_one('a').get('href')
        except:
            user = "0"
        try:
            date = header.select_one("time").get("datetime")
            date = date.split("+")
            date = date[0]
        except:
            date = "0"
        return user, title, date

    #this function is implicit. Takes string or string list(as it joins them into single string) clears them
    def clear_unnecesser_characters(self, s):
        if isinstance(s , str):
            return re.sub("[^\w.]+", " ", s)
        if isinstance(s , list):
            return re.sub("[^\w.]+", " ", ''.join(s))

    def get_content_by_sections(self, bs):
        content = []
        sections = bs.find_all('section')
        for section in sections:
            for heads in section.find_all('h2'):
                content.append(heads.get_text())
            paragraphs = section.find_all('figcaption')
            for paragraph in paragraphs:
                content.append(paragraph.get_text())
            for p in section.find_all('p'):
                content.append((p.get_text()))
        return self.clear_unnecesser_characters(content)

    def page_count(self, bs):
        # With more then 1 pages "next" button added to the list so number must decreased by 1.
        try:
            num = int(bs.select_one('div.pagination').find_all('li')[-2].get_text())
        except:
            num = 1
        return num

    def jason_creater(self, data):
        d = dict()
        d['url'] = data.url
        d['title'] = data.title
        d['date'] = data.publish_date
        d['content'] = data.content
        d['source'] = { 'name' : data.source.name, 'domain' : data.source.domain , 'favicon' : data.source.favicon}
        return d

    def crawler(self, keyword, time = None):
        result = []
        bs = self.get_beautiful_html(self.domain_handler(keyword, time))
        #Gets page count
        p_count = self.page_count(bs)
        urls = self.search_href(bs)
        for url in urls:
            bs_r = self.get_beautiful_html(url)
            name, title, date = self.get_header(bs_r)
            content = self.get_content_by_sections(bs_r)
            source = Source(name, self.domain, self.favicon)
            if title is not "0":
                result.append(Content(url, title, date, content, source).jason_creater())
        # Applies the process to other pages if there is!
        if p_count > 1:
            for i in range(2 ,p_count):
                bs = self.get_beautiful_html(self.domain_handler(keyword, time, i))
                urls = self.search_href(bs)
                for url in urls:
                    bs_r = self.get_beautiful_html(url)
                    name, title, date = self.get_header(bs_r)
                    content = self.get_content_by_sections(bs_r)
                    source = Source(name, self.domain, self.favicon)
                    if title is not "0":
                        result.append(Content(url, title, date, content, source).jason_creater())
        return result


if __name__ == "__main__":
    result = OnedioCrawler().crawler("sevgi")
    for n,i in enumerate(result):
        print(n, " ----- ",i)

    with open('results.json', 'w', encoding= 'utf-8') as rf:
        json.dump(result, rf, ensure_ascii=False)

