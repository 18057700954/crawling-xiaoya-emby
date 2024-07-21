# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/i
# tem-pipeline.html
import os.path

from .items import EmbyxiaoyaproItem, XiaoyaStrmItem
from scrapy.pipelines.files import FilesPipeline
import scrapy

import aiofiles
import asyncio
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


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
    def open_spider(self, spider):
        self.sys = os.name

    def process_item(self, item, spider):
        if isinstance(item, XiaoyaStrmItem):
            task = [asyncio.create_task(self.write_file(item["path"][i], item["content"][i])) for i in
                    range(len(item["path"]))]
            asyncio.gather(*task)

    async def write_file(self, p, content):
        if self.sys == "nt":
            p = p.replace("|", "-")
        try:
            rp = p.rfind("/")
            if not os.path.exists(p[:rp]):
                os.makedirs(p[:rp], exist_ok=True)
            async with aiofiles.open(p, mode='w', encoding="utf-8") as f:
                await f.write(content)
        except Exception as e:
            print(f"XiaoyaToStrmPipeline-write_file{str(e)}")
