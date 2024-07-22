import os
import json
import scrapy

from ..settings import XIAOYA_EMBY_CONFIG
from ..items import XiaoyaStrmItem


class XiaoyaaliststrmSpider(scrapy.Spider):
    system_platform = os.name
    name = "xiaoyaAlistStrm"
    allowed_domains = [""]
    token = ""

    def start_requests(self):
        if not self.start_urls and hasattr(self, "start_url"):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)"
            )
        yield scrapy.Request(url=XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/auth/login",
                             method="post",
                             dont_filter=True,
                             body=json.dumps(XIAOYA_EMBY_CONFIG["XIAOYA_LOGIN"]),
                             headers={'Content-Type': 'application/json'},
                             encoding="utf-8")

    def parse(self, response, **kwargs):
        j = json.loads(response.text)
        self.token = j['data']['token']
        scan_dir = XIAOYA_EMBY_CONFIG["SCAN_DIR"]
        url = XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/fs/list"
        header = {"Authorization": f"{self.token}", 'Content-Type': 'application/json; charset=utf-8'}
        for d in scan_dir:
            b_data = {
                "path": d,
                "password": "",
                "page": 1,
                "per_page": 0,
                "refresh": False
            }
            yield scrapy.Request(url, method="post", dont_filter=True, headers=header, body=json.dumps(b_data),
                                 meta={'body_data': b_data}, callback=self.parse2, encoding="utf-8")

    def parse2(self, response):
        body_data = response.meta['body_data']
        if body_data["path"] not in XIAOYA_EMBY_CONFIG["EXCLUDE_DIR"]:
            data = json.loads(response.text)["data"]["content"]
            url = XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/fs/list"
            header = {"Authorization": f"{self.token}", 'Content-Type': 'application/json; charset=utf-8'}
            if data:
                files = XiaoyaStrmItem()
                files["path"], files["content"] = [], []
                for d in data:
                    if d["is_dir"]:
                        b_data = {
                            "path": f"{body_data['path']}/{d['name']}",
                            "password": "",
                            "page": 1,
                            "per_page": 0,
                            "refresh": False
                        }
                        yield scrapy.Request(url, method="post", dont_filter=True, headers=header,
                                             body=json.dumps(b_data),
                                             meta={'body_data': b_data}, callback=self.parse2, encoding="utf-8")
                    else:
                        e = d["name"].rfind(".")
                        p_cache = f"{body_data['path']}/{d['name'][:e]}.strm"
                        if self.system_platform == "nt":  # 保存的文件名
                            p = f"{XIAOYA_EMBY_CONFIG['SCAN_SAVE_DIR']}" + p_cache.replace("|", "-").replace(":", "：")
                        else:
                            p = f"{XIAOYA_EMBY_CONFIG['SCAN_SAVE_DIR']}{p_cache}"
                        c = f"{XIAOYA_EMBY_CONFIG['XIAOYA_ADDRESS']}/d{body_data['path']}/{d['name']}"  # 保存的内容
                        if d["name"].endswith(XIAOYA_EMBY_CONFIG["M_EXT"]) and not os.path.exists(p):  # 判断文件是视频，并且不存在
                            files["path"].append(p)
                            files["content"].append(c)
                if files["path"]:
                    yield files
        else:
            print("已排除：" + body_data["path"])
