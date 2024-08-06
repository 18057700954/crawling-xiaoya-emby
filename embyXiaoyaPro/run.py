import os
# import argparse
from argparse import ArgumentParser

from scrapy.cmdline import execute

if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('-s', '--spider', required=False, help='spider', default='xiaoyaEmby')
    args = arg_parser.parse_args()
    print(f"运行 {args.spider}")
    try:
        execute(f"scrapy crawl {args.spider}".split())
    except Exception as e:
        print(f"{str(e)}")
