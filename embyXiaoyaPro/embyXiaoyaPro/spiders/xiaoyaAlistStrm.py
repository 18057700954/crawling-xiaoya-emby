import asyncio
import os
import json
import sqlite3

import aiofiles
import aiosqlite
import scrapy
from urllib.parse import unquote
from ..settings import XIAOYA_EMBY_CONFIG
from ..items import XiaoyaStrmItem
from ..tools import sha256_hash


class XiaoyaaliststrmSpider(scrapy.Spider):
    name = "xiaoyaAlistStrm"
    allowed_domains = [""]
    api_list_url = XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/fs/list"
    api_login_url = XIAOYA_EMBY_CONFIG["XIAOYA_ADDRESS"] + "/api/auth/login"

    @staticmethod
    async def create_table(db, table_name, create_sql):
        try:
            async with db.execute(
                    f'''SELECT name FROM sqlite_master where type="table" and name="{table_name}";''') as cursor:
                if await cursor.fetchone() is None:
                    print("create table", table_name)
                    await db.execute(create_sql)
                    await db.commit()
                    return True
        except Exception as e:
            print(f"create table {table_name} failed: {e}")

    async def create_db(self):
        create_table_info_sql = '''CREATE TABLE IF NOT EXISTS info ("localAdd" varchar(255) NOT NULL,"remoteAdd" varchar(255) NOT NULL,PRIMARY KEY ("localAdd"));'''
        create_table_files_sql = '''CREATE TABLE IF NOT EXISTS files ("filename" varchar(255) NOT NULL,"md5" varchar(100) NOT NULL,PRIMARY KEY ("filename"));'''
        async with aiosqlite.connect("./StrmFiles.db") as db:
            await self.create_table(db, "files", create_table_files_sql)
            c_info = await self.create_table(db, "info", create_table_info_sql)
            await asyncio.sleep(1)
            if c_info:
                info_sql = "insert or replace into info (localAdd, remoteAdd) values(?,?)"
                files_sql = "insert or replace into files (filename, md5) values(?,?)"
                for root, dirs, files in os.walk(XIAOYA_EMBY_CONFIG['SCAN_SAVE_DIR']):
                    if ".cache" in root:
                        continue
                    print(root)
                    fi = [file for file in files if file.endswith(".strm")]
                    if fi:
                        async with aiofiles.open(os.path.join(root, fi[0]), 'r', encoding='utf-8') as f1:
                            info_read = unquote(await f1.read()).replace("http://xiaoya.host:5678/d", "")
                            info_path, info_name = os.path.split(info_read)
                            await db.execute(info_sql, (root, info_path))
                        for files_fi in fi:
                            async with aiofiles.open(os.path.join(root, files_fi), 'r', encoding='utf-8') as f2:
                                files_read = unquote(await f2.read()).replace("http://xiaoya.host:5678/d", "")
                                files_path, files_name = os.path.split(files_read)
                                files_name_start, files_name_end = os.path.splitext(files_name)
                                strm_file_name = f"{files_name_start}.strm"
                                sha256 = await sha256_hash(strm_file_name)
                                await db.execute(files_sql, (f"{files_path}/{strm_file_name}", sha256))
                        await db.commit()

    def __init__(self, **kwargs):
        self.filesDB = sqlite3.connect("./StrmFiles.db")
        self.system_platform = os.name
        self.token = ""
        self.header = {}
        asyncio.run(self.create_db())
        super().__init__(**kwargs)

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

    async def parse2(self, response):
        body_data = response.meta['body_data']
        # print(body_data["path"])
        if not str(body_data["path"]).startswith(tuple(XIAOYA_EMBY_CONFIG["EXCLUDE_DIR"])):
            data = json.loads(response.text)["data"]["content"]
            if data:
                item_files = XiaoyaStrmItem()
                item_files["content"], item_files["pathCache"] = [], []
                for d in data:
                    if d["is_dir"]:  # 是目录
                        b_data = {"path": f"{body_data['path']}/{d['name']}", "password": "",
                                  "page": 1, "per_page": 0, "refresh": False}
                        yield scrapy.Request(self.api_list_url, method="post", headers=self.header,
                                             body=json.dumps(b_data), meta={'body_data': b_data},
                                             callback=self.parse2, encoding="utf-8", dont_filter=True)
                    elif d["name"].endswith(XIAOYA_EMBY_CONFIG["M_EXT"]):  # 视频文件
                        name_start, name_end = os.path.splitext(d["name"])
                        strm_file_name = f"{body_data['path']}/{name_start}.strm"  # 文件路径/文件名
                        strm_file_content = f"http://xiaoya.host:5678/d{body_data['path']}/{d['name']}"  # 保存的文件内容
                        strm_file_content_hash = await sha256_hash(strm_file_content)  # 文件内容sha256_hash值
                        select_sql = f'select * from files where filename="{strm_file_name}"'
                        row = self.filesDB.execute(select_sql).fetchone()
                        if row is None or (row[1] != strm_file_content_hash):
                            item_files["pathCache"].append(strm_file_name)
                            item_files["content"].append(strm_file_content)
                if item_files["pathCache"]:
                    yield item_files
        else:
            print("已排除：" + body_data["path"])

    def __del__(self):
        self.filesDB.close()
