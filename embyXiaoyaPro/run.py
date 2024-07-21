import os

from scrapy.cmdline import execute

if __name__ == '__main__':
    spiders = os.listdir("./embyXiaoyaPro/spiders")[::-1][2:]
    [print("{:<6}{}".format(s, spiders[s])) for s in range(len(spiders))]
    print("[请输入序号] :", end="")
    a = input("")
    try:
        execute(f"scrapy crawl {spiders[int(a)][:-3]}".split())
    except Exception as e:
        print(f"你TM傻逼吧！只能选0-{len(spiders)}")
