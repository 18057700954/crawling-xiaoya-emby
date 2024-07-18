# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/i
# tem-pipeline.html

from scrapy.pipelines.files import FilesPipeline
import scrapy

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class DownLoadingPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for url, filename in zip(item["urls"], item["filename"]):
            a = url.rfind("/")
            referer = url[:a]
            yield scrapy.Request(url, meta={"filename": filename}, headers={"Referer": referer},
                                 dont_filter=True, encoding="utf-8")

    def file_path(self, request, response=None, info=None, *, item=None):
        return request.meta["filename"]

    def item_completed(self, results, item, info):
        try:
            for i in results:
                if i[0]:
                    print(i[1])
                else:
                    print(i[1])
        except Exception as e:
            print(f"DownLoadingPipeline-{str(e)}")
        return item
