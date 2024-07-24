import os
import argparse

from scrapy.cmdline import execute

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--spider', required=False, help='spider', default='xiaoyaEmby')
    args = arg_parser.parse_args()
    print(args.spider)
    try:
        execute(f"scrapy crawl {args.spider}".split())
    except Exception as e:
        print(f"{str(e)}")
