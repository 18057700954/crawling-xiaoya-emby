# Scrapy settings for embyXiaoyaPro project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "embyXiaoyaPro"
SPIDER_MODULES = ["embyXiaoyaPro.spiders"]
NEWSPIDER_MODULE = "embyXiaoyaPro.spiders"

LOG_LEVEL = "ERROR"  # ERROR INFO DEBUG

DOWNLOAD_TIMEOUT = 180  # 下载超时时间
REACTOR_THREADPOOL_MAXSIZE = 100  # scrapy通过一个线程池来进行DNS查询，增大这个线程池一般也可以提高scrapy性能。
MEDIA_ALLOW_REDIRECTS = True  # 处理重定向
# HTTPERROR_ALLOWED_CODES = [301, 302, 304]  # 处理其他状态码
RETRY_ENABLED = True  # 打开重试开关
RETRY_TIMES = 2  # 重试次数

XIAOYA_EMBY_CONFIG = {
    # 爬取xiaoya alist 生成strm配置
    "XIAOYA_LOGIN": {"username": "dav", "password": "20030512"},
    "XIAOYA_ADDRESS": "http://localhost:5678",
    "token": "",
    "SCAN_DIR": [  # 扫描的地址
        "/每日更新/动漫/国漫/2024"
    ],
    "EXCLUDE_DIR": [  # 排除的目录
        "/每日更新/PikPak",
        "/每日更新/爽文短剧",
        "/每日更新/音乐",
        "/每日更新/纪录片",
        "/每日更新/动漫/国漫/所有",
        "/每日更新/动漫/日本/所有",
    ],
    # 爬取emby.xiaoya.pro元数据配置
    "SCAN_SAVE_DIR": "E:\docker\emby\media\\xiaoya",  # strm 文件 保存路径

    "S_PATHS": [  # 网站元数据爬取开始路径
        "每日更新/"
    ],
    "M_EXT": (".mkv", ".mp4", ".flv", ".wmv"),
    "T_EXT": (".nfo", ".strm", ".ass", ".srt", ".ssa"),
    "I_EXT": (".png", ".img", ".jpg"),
    "S_DOMAIN": [
        "https://emby.xiaoya.pro/",
        "https://icyou.eu.org/",
        "https://lanyuewan.cn/",
        "https://emby.8.net.co/",
        "https://emby.raydoom.tk/",
        "https://emby.kaiserver.uk/",
        "https://embyxiaoya.laogl.top/",
        "https://emby-data.raydoom.tk/",
        "https://emby-data.ermaokj.com/",
        "https://emby-data.poxi1221.eu.org/",
        "https://emby-data.ermaokj.cn/",
        "https://emby-data.bdbd.fun/",
        "https://emby-data.wwwh.eu.org/",
        "https://emby-data.f1rst.top/",
        "https://emby-data.ymschh.top/",
        "https://emby-data.wx1.us.kg/",
        "https://emby-data.r2s.site/",
        "https://emby-data.neversay.eu.org/",
        "https://emby-data.800686.xyz/"
    ],
}

FILES_STORE = "C:/PersonalData/docker/emby/media/xiaoya"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 500

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.05
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 100
# CONCURRENT_REQUESTS_PER_IP = 256

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#     "embyXiaoyaPro.middlewares.ProxyDownloaderMiddleware": 100,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "embyXiaoyaPro.middlewares.UArandom": 100,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#     "scrapy.extensions.logstats.LogStats": 500,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # "embyXiaoyaPro.pipelines.EmbyxiaoyaproPipeline": 300,
    "embyXiaoyaPro.pipelines.DownLoadingPipeline": 301,
    "embyXiaoyaPro.pipelines.XiaoyaToStrmPipeline": 302
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
