import os

from scrapy.cmdline import execute


def select():
    spiders = os.listdir("./embyXiaoyaPro/spiders")[:-2]
    [print("{:<6}{}".format(s, spiders[s])) for s in range(len(spiders))]
    print("\033[32m[请输入序号] :", end="")
    a = input("")
    try:
        execute(f"scrapy crawl {spiders[int(a)]}".split())
    except Exception as e:
        print(f"\033[1m\033[31m你TM傻逼吧！只能选0-{len(spiders)}")


if __name__ == '__main__':
    select()