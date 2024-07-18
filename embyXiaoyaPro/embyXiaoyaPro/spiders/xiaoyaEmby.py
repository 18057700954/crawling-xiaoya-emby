import os
import random

import requests
import scrapy
from urllib.parse import unquote
from ..items import EmbyxiaoyaproItem
from ..settings import S_PATHS, T_EXT, I_EXT, S_DOMAIN, FILES_STORE


class XiaoyaembySpider(scrapy.Spider):
    domains_pool = []
    name = "xiaoyaEmby"
    EXT = T_EXT + I_EXT
    allowed_domains = [d.replace("https://", "").replace("/", "") for d in S_DOMAIN]
    start_urls = ["https://emby.xiaoya.pro/" + i for i in S_PATHS]

    def test_internet_speed(self, url):
        try:
            response = requests.head(url, timeout=1)
            if response.status_code == 200:
                self.domains_pool.append(url)
        except requests.exceptions.RequestException as e:
            print(f"test_internet_speed -> {str(e)}")

    def parse(self, response, **kwargs):
        [self.test_internet_speed(p) for p in S_DOMAIN]
        if not self.domains_pool:
            self.domains_pool = ["https://emby.xiaoya.pro/"]
        lists = response.xpath("//a/text()").extract()[1::]
        for li in lists:
            url = response.urljoin(li)
            if li.endswith("/"):
                print("--" + li)
                yield scrapy.Request(url, callback=self.parse2, dont_filter=True)

    def parse2(self, response):
        # print(unquote(response.url))
        ditem = EmbyxiaoyaproItem()
        ditem["urls"] = []
        ditem["filename"] = []
        ditem["filesize"] = []
        lists = response.xpath("//a/text()").extract()[1::]
        s = response.xpath("//pre/text()").extract()[1::]
        file_size_list = [i.split(" ")[-1][:-2] for i in s]
        try:
            for li, size in zip(lists, file_size_list):
                url = response.urljoin(li)
                filename = unquote(url.replace("https://emby.xiaoya.pro", ""))
                if li.endswith("/"):  # 目录
                    yield scrapy.Request(url, callback=self.parse2, dont_filter=True)
                elif li.endswith(self.EXT):  # 文件
                    file_path = FILES_STORE + filename
                    url = url.replace("https://emby.xiaoya.pro/", random.choice(self.domains_pool))
                    if os.path.exists(file_path):  # 文件存在
                        file_size = os.path.getsize(file_path)
                        if int(size) != int(file_size):  # 基于文件大小判断更新
                            os.remove(file_path)
                            ditem["urls"].append(url)
                            ditem["filename"].append(filename)
                            ditem["filesize"].append(size)
                    else:
                        ditem["urls"].append(url)
                        ditem["filename"].append(filename)
                        ditem["filesize"].append(size)
            yield ditem
        except Exception as e:
            print(f"parse2->{str(e)}")
