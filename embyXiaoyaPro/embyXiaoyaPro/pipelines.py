# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/i
# tem-pipeline.html
import logging
import os.path
import re

from .items import EmbyxiaoyaproItem, XiaoyaStrmItem
from scrapy.pipelines.files import FilesPipeline
import scrapy
import asyncio
import sqlite3
import aiofiles
from sqlite3 import OperationalError
from .settings import XIAOYA_EMBY_CONFIG
from .tools import sha256_hash


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
        if spider.name == "xiaoyaAlistStrm":
            self.root_dir = XIAOYA_EMBY_CONFIG["SCAN_SAVE_DIR"]
            self.connect_db()

    def close_spider(self, spider):
        if spider.name == "xiaoyaAlistStrm":
            self.cursor.close()
            self.db.close()
            print("close db")

    def connect_db(self):
        print("connect db")
        create_table = "CREATE TABLE IF NOT EXISTS files ('filename' varchar(255) NULL,'md5' varchar(255) NULL,PRIMARY KEY ('filename'))"
        self.db = sqlite3.connect("./StrmFiles.db")
        try:
            self.cursor = self.db.execute("select * from files")
        except OperationalError as e:
            logging.error(f"{e}")
            self.db.execute(create_table)
            self.db.commit()

    async def process_item(self, item, spider):
        if isinstance(item, XiaoyaStrmItem):
            tasks = []
            for c, pc in zip(item["content"], item["pathCache"]):
                tasks.append(asyncio.create_task(self.write_file(c, pc)))
            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            # 插入数据库
            # sql = "insert or replace into files (filename, md5) values "
            # for task in done:
            #     print(f"download succeed {task.result()[0]}")
            #     sql += f"('{task.result()[0]}', '{task.result()[1]}'),"
            # self.db.execute(sql[:-1])
            # self.db.commit()
        return item

    async def write_file(self, content, ca):
        index = 999
        p = ca.replace("_Tacit0924", "")
        p_list = p.split("/")
        pattern = r"^(S|Season)(?: )?\d+$"
        if re.match(pattern, p_list[-2]):
            index = -2
        else:
            index = -1
        try:
            video_name = p_list[index - 1].split(".")[1]
        except:
            video_name = p_list[index - 1].split(".")[0]
        file_path = os.path.join(self.root_dir, os.path.join(*p_list[:index - 1]))
        video_name_list = []
        try:
            file_path_list = os.scandir(file_path)
            for dir in file_path_list:
                if dir.is_dir() and dir.name.startswith(video_name):
                    video_name_list.append(dir.name)
        except Exception as e:
            print(f"write_file—— 116{str(e)}")
        if not video_name_list:
            video_dir = os.path.join(self.root_dir, *p_list)
        else:
            v_name = min(video_name_list, key=lambda x: len(x))
            video_dir = os.path.join(file_path, v_name, *p_list[index:])
        # 存储
        try:
            rp = video_dir.replace(p_list[-1], "")
            if not os.path.exists(rp):
                os.makedirs(rp, exist_ok=True)
            async with aiofiles.open(video_dir, mode='w', encoding="utf-8") as f:
                await f.write(content)
            sha = sha256_hash(content)
            return ca, sha
        except Exception as e:
            print(f"write_file—— -1{str(e)}")
