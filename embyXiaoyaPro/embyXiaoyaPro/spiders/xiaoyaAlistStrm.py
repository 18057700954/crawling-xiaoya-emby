import os
import json
import sqlite3

import scrapy

from ..settings import XIAOYA_EMBY_CONFIG
from ..items import XiaoyaStrmItem
from ..tools import sha256_hash


class XiaoyaaliststrmSpider(scrapy.Spider):
    system_platform = os.name
    db = sqlite3.connect("./StrmFiles.db")
    name = "xiaoyaAlistStrm"
    allowed_domains = [""]
    api_list_url = XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/fs/list"
    api_login_url = XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/auth/login"
    token = ""
    header = ""

    def start_requests(self):
        if not self.start_urls and hasattr(self, "start_url"):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)"
            )
        yield scrapy.Request(url=self.api_login_url, method="post", dont_filter=True,
                             body=json.dumps(XIAOYA_EMBY_CONFIG["XIAOYA_LOGIN"]),
                             headers={'Content-Type': 'application/json'}, encoding="utf-8", callback=self.parse)

    def parse(self, response, **kwargs):
        j = json.loads(response.text)
        self.token = j['data']['token']
        self.header = {"Authorization": f"{self.token}", 'Content-Type': 'application/json; charset=utf-8'}
        scan_dir = XIAOYA_EMBY_CONFIG["SCAN_DIR"]
        for d in scan_dir:
            b_data = {"path": d, "password": "", "page": 1, "per_page": 0, "refresh": False}
            yield scrapy.Request(self.api_list_url, method="post", dont_filter=True, headers=self.header,
                                 body=json.dumps(b_data), meta={'body_data': b_data}, callback=self.parse2,
                                 encoding="utf-8")

    def parse2(self, response):
        body_data = response.meta['body_data']
        if body_data["path"] not in XIAOYA_EMBY_CONFIG["EXCLUDE_DIR"]:
            data = json.loads(response.text)["data"]["content"]
            if data:
                files = XiaoyaStrmItem()
                files["content"], files["pathCache"] = [], []
                for d in data:
                    if d["is_dir"]:  # 目录
                        b_data = {"path": f"{body_data['path']}/{d['name']}", "password": "",
                                  "page": 1, "per_page": 0, "refresh": False}
                        yield scrapy.Request(self.api_list_url, method="post", headers=self.header,
                                             body=json.dumps(b_data), meta={'body_data': b_data},
                                             callback=self.parse2, encoding="utf-8", dont_filter=True)
                    elif d["name"].endswith(XIAOYA_EMBY_CONFIG["M_EXT"]):  # 文件是视频
                        # if d["name"].endswith(XIAOYA_EMBY_CONFIG["M_EXT"]):  # 判断文件是视频
                        e = d["name"].rfind(".")
                        strm_path = f"{body_data['path']}/{d['name'][:e]}.strm"  # 文件名
                        if self.system_platform == "nt":
                            strm_path = strm_path.replace("|", "-").replace(":", "-")
                        # file_save_path = f"{XIAOYA_EMBY_CONFIG['SCAN_SAVE_DIR']}{strm_path}"  # 保存的文件名
                        file_content = f"{XIAOYA_EMBY_CONFIG['XIAOYA_ADDRESS']}/d{body_data['path']}/{d['name']}"  # 保存的文件内容
                        c_hash = sha256_hash(file_content)  # 文件内容sha256_hash值
                        select_sql = f"select * from files where filename='{strm_path}'"
                        cursor = self.db.execute(select_sql)
                        rows = cursor.fetchone()
                        if rows is None or rows[1] != c_hash:
                            # files["path"].append(file_save_path)
                            files["pathCache"].append(strm_path)
                            files["content"].append(file_content)
                if files["pathCache"]:
                    yield files
        else:
            print("排除：" + body_data["path"])

    def __del__(self):
        self.db.close()
