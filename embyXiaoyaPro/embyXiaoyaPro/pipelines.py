# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/i
# tem-pipeline.html
import logging
import os.path
from .items import EmbyxiaoyaproItem, XiaoyaStrmItem
from .tools import sha256_hash
from scrapy.pipelines.files import FilesPipeline
import scrapy
import aiofiles
import asyncio
import sqlite3
from aiosqlite import OperationalError


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter

class DownLoadingPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        if isinstance(item, EmbyxiaoyaproItem):
            for url, filename in zip(item["urls"], item["filename"]):
                a = url.rfind("/")
                referer = url[:a]
                yield scrapy.Request(url, meta={"filename": filename}, headers={"Referer": referer},
                                     dont_filter=True, encoding="utf-8")
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        try:
            if response is None:
                print("response is None: url:", request.url)
            return request.meta["filename"]
        except Exception as e:
            print(f"DownLoadingPipeline-file_path{str(e)}")

    def item_completed(self, results, item, info):
        try:
            for i in results:
                if i[0]:
                    print(f"download succeed {i[1]['path']}")
                else:
                    print(f"{i[1]}-{item}")
        except Exception as e:
            print(f"DownLoadingPipeline-item_completed{str(e)}")
        return item


class XiaoyaToStrmPipeline:

    def __init__(self):
        self.db = None
        self.cursor = None

    def open_spider(self, spider):
        self.connect_db()
        # asyncio.ensure_future(self.connect_db())

    def close_spider(self, spider):
        self.close_db()

    def close_db(self):
        self.cursor.close()
        self.db.close()

    def connect_db(self):
        print("connect db")
        create_table = "CREATE TABLE IF NOT EXISTS files ('filename' varchar(255) NULL,'md5' varchar(255) NULL,PRIMARY KEY ('filename'))"
        self.db = sqlite3.connect("./StrmFiles.db")
        try:
            self.cursor = self.db.execute('SELECT * FROM files')
        except OperationalError as e:
            logging.error(f"{e}")
            self.db.execute(create_table)
            self.db.commit()

    async def process_item(self, item, spider):
        if isinstance(item, XiaoyaStrmItem):
            tasks = []
            for p, c, pc in zip(item["path"], item["content"], item["pathCache"]):
                tasks.append(asyncio.create_task(self.write_file(p, c, pc)))
            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            sql = "insert or replace into files (filename, md5) values "
            for task in done:
                print(f"download succeed {task.result()[0]}")
                sql += f"('{task.result()[0]}', '{task.result()[1]}'),"
            self.db.execute(sql[:-1])
            self.db.commit()
        return item

    async def write_file(self, p, content, ca):
        try:
            rp = p.rfind("/")
            if not os.path.exists(p[:rp]):
                os.makedirs(p[:rp], exist_ok=True)
            async with aiofiles.open(p, mode='w', encoding="utf-8") as f:
                await f.write(content)
            sha = sha256_hash(content)
            return ca, sha
        except Exception as e:
            print(f"XiaoyaToStrmPipeline-write_file{str(e)}")
