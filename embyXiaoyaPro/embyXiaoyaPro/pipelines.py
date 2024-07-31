# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/i
# tem-pipeline.html
import logging
import os.path
import re
import shutil
from distutils import dir_util

import aiosqlite

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
        if isinstance(item, EmbyxiaoyaproItem):
            try:
                return request.meta["filename"]
            except Exception as e:
                print(f"DownLoadingPipeline-file_path{str(e)}")

    def item_completed(self, results, item, info):
        if isinstance(item, EmbyxiaoyaproItem):
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

    def open_spider(self, spider):
        if spider.name == "xiaoyaAlistStrm":
            self.root_dir = XIAOYA_EMBY_CONFIG["SCAN_SAVE_DIR"]
            self.connect_db()
            # self.cache_save()

    def close_spider(self, spider):
        if spider.name == "xiaoyaAlistStrm":
            self.cache_save()
            self.db.close()
            print("close db")

    def connect_db(self):
        print("connect db")
        self.db = sqlite3.connect("./StrmFiles.db")

    def cache_save(self):
        cache_path = os.path.join(XIAOYA_EMBY_CONFIG["SCAN_SAVE_DIR"], ".cache")
        try:
            for root, dirs, files in os.walk(cache_path):
                is_scrape = False
                if files:
                    for f in files:
                        if not f.endswith(".strm"):
                            is_scrape = True
                            break
                    if not is_scrape:
                        print(f"\033[31m等待刮削 -> {root}\033[0m")
                if is_scrape:
                    root_split = root.split(".cache")
                    new_path = os.path.join(root_split[0][:-1], root_split[1][1:])
                    try:
                        dir_util.copy_tree(root, new_path)
                        dir_util.remove_tree(root)
                        # shutil.copytree(root, new_path)
                        # shutil.rmtree(root)
                    except FileExistsError:
                        logging.error(f"目标目录 {new_path} 已存在")
                        # print(f"目标目录 {new_path} 已存在")
                    except Exception as e:
                        logging.error(f"{str(e)}")
                        print(f"{str(e)}")
                    for r2, d2, f2 in os.walk(new_path):
                        try:
                            strmFileOne = [j for j in f2 if j.endswith(".strm")][0]
                        except IndexError:
                            strmFileOne = None
                        if strmFileOne:
                            with open(os.path.join(r2, strmFileOne), "r", encoding="utf-8") as f:
                                # print("strmFile",r2, strmFileOne)
                                con = f.read()
                                con_add = con.replace("http://xiaoya.host:5678/d", "")
                                con_add, _ = os.path.split(con_add)
                                # print(new_path, con_add)
                                self.db.execute("insert or replace into info (localAdd, remoteAdd) values(?,?)",
                                                (r2, con_add))
                                self.db.commit()
        except Exception as e:
            print(f"XiaoyaToStrmPipeline-close_spider{str(e)}")

    async def process_item(self, item, spider):
        if isinstance(item, XiaoyaStrmItem):
            async with aiosqlite.connect("./StrmFiles.db") as Strmdb:
                tasks = []
                for c, pc in zip(item["content"], item["pathCache"]):
                    tasks.append(asyncio.create_task(self.write_file(c, pc, Strmdb)))
                done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                # 插入数据库
                sql = '''insert or replace into files (filename, md5) values '''
                for task in done:
                    print(f"download succeed {task.result()[0]}")
                    sql += f'("{task.result()[0]}", "{task.result()[1]}"),'
                await Strmdb.execute(sql[:-1])
                await Strmdb.commit()
        return item

    async def write_file(self, content, strm_file, Strmdb):
        # print(strm_file)
        strm_file_path, strm_file_name = os.path.split(strm_file)
        async with Strmdb.execute(f'select * from info where remoteAdd="{strm_file_path}"') as cur:
            add_row = await cur.fetchone()
            if add_row:
                save_file_name = os.path.join(add_row[0], strm_file_name)
            else:
                save_file_name = os.path.join(XIAOYA_EMBY_CONFIG["SCAN_SAVE_DIR"], ".cache", *strm_file.split("/"))

            # 存储
            # r_save_file_name = save_file_name
            if os.name == "nt":
                save_file_name = save_file_name.replace("|", "")
            try:
                save_file_path, _ = os.path.split(save_file_name)
                if not os.path.exists(save_file_path):
                    os.makedirs(save_file_path, exist_ok=True)
                async with aiofiles.open(save_file_name, mode='w', encoding="utf-8") as f:
                    await f.write(content)
                sha = await sha256_hash(content)
                return strm_file, sha
            except Exception as e:
                print(f"write_file —— -1{str(e)}")
