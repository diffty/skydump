import re
import logging

from dataclasses import asdict

from skydump import parse_page, parse_css, find_mimetype
from skydump import parse_url, crawl_page, crawl_css, open_resource_manifest
from skydump import download, get_resource_local_url, remap_html_page


logging.getLogger().setLevel(logging.INFO)


BLACKLIST_SUBDOMAINS = [
    "www",
    "lequipe-skyrock",
    "music",
    "cine",
    "sport",
    "fr",
    "en",
]


ALLOW_CRAWL_CONDITIONS = [
    re.compile(r"[a-zA-Z0-9\-]+\.skyrock\.com", re.I),
]

FORBID_CRAWL_CONDITIONS = [
    re.compile(r"(?:(?:" + "|".join(BLACKLIST_SUBDOMAINS) + r")\.skyrock\.com|sk.mu)", re.I),
]

#page = parse_page(START_URL, ALLOW_CRAWL_CONDITIONS, FORBID_CRAWL_CONDITIONS)

#print("==== LINKS ====")
#for l in page.links:
#    print("Remote URL:" + l.remote_url)
#    print("Local URL:" + l.local_url)
#    print("Origin:" + l.origin)
#    print("Type:" + str(l.type))
#    print()

#t = parse_url("/2.html")
#t = parse_url("https://www.skyrock.com")
#t = parse_url("https://www.skyrock.com/")
#t = parse_url("https://www.skyrock.com/inxed.tmlh")
#t = parse_url("https://www.skyrock.com/blog")
#t = parse_url("https://www.skyrock.com/blog/")
#t = parse_url("https://www.skyrock.com/blog/test")
#t = parse_url("https://www.skyrock.com/blog/testent/")
#t = parse_url("https://www.skyrock.com/blog/E.re")
#t = parse_url("https://www.skyrock.com/blog/cybercop.php")
#t = parse_url("https://www.skyrock.com/blog/cybercop.php?id=11211&url=https://lbb.skyrock.com/")
#t = parse_url("https://www.skyrock.com/blog/?id=11211&url=https://lbb.skyrock.com/")
#t = parse_url("https://www.skyrock.com/?id=11211&url=https://lbb.skyrock.com/")


#print(find_mimetype("application/vnd.openxmlformats-officedocument.presentationml.presentation"))
#print(find_mimetype("text/html; charset=UTF-8"))
#print(find_mimetype("yeeeeauotajzo\"3^é''éù ; text/html; charset=UTF-8"))

#p = open_resource_manifest("D:/Users/DiFFtY/Documents/_Projets/Divers/2023_06_Skydump/workspace/pips.skyrock.com/6969696-posted-on-2009-02-10.json")
#p = open_resource_manifest("D:/Users/DiFFtY/Documents/_Projets/Divers/2023_06_Skydump/workspace/pips.skyrock.com/rss.xml.json")
#print(p)

#print(get_resource_local_url("https://pips.skyrock.com"))
#print(get_resource_local_url("/1.html"))

#download("https://pips.skyrock.com/", "test.html")

REG_URL_NO_PROTOCOL = re.compile(r"^([a-zA-Z]+://)?([^\/]*)(\/[^?]*)?(\?.*)?", re.I)

START_URL = "https://xxzevent2020xx.skyrock.com/"

already_crawled = set()
to_crawl = [START_URL]


#user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"


while len(to_crawl) > 0:
    url = to_crawl.pop(0)

    with open("to_crawl.txt", "w") as fp:
        fp.write("\n".join(to_crawl))

    print(f"---- GETTING PAGE {url} ----")
    page = crawl_page(url, ALLOW_CRAWL_CONDITIONS, FORBID_CRAWL_CONDITIONS)
    already_crawled.add(url)

    for l in page.links:
        if l.resource.remote_url not in already_crawled \
            and l.resource.remote_url not in to_crawl \
            and l.resource.type == "page" \
            and "connect=1" not in l.resource.remote_url \
            and all(map(lambda r: r.search(l.resource.remote_url) is not None, ALLOW_CRAWL_CONDITIONS)) and all(map(lambda r: r.search(l.resource.remote_url) is None, FORBID_CRAWL_CONDITIONS)):

            to_crawl.append(l.resource.remote_url)
    
    url_reg = REG_URL_NO_PROTOCOL.search(url)
    if not url_reg:
        raise Exception(f"Can't parse resource url: {url}")
    
    curr_domain = url_reg.group(1) + url_reg.group(2)
    to_crawl = sorted(to_crawl, key=lambda u: u.startswith(curr_domain), reverse=True)


#css_rsc = crawl_css("https://static.skyrock.net/css/blogs/120.css?eSaHpY_93")
#css_rsc = crawl_css("https://static.skyrock.net/css/blogs/tpl.css?eFC2Ei1R6")
#css_rsc = crawl_css("https://static.skyrock.net/css/blogs/421.css?e2Ikr0XNQ")
#css_rsc = crawl_css("https://static.skyrock.net/css/m/common.css?e3Cyph8r0")
#css_rsc = crawl_css("https://static.skyrock.net/css/front.css_eEHy_Q-LU.css")

#remap_html_page("static.skyrock.net/css/common.css_er9WKMvqR.css",
#                "/img/loader/wait-horizontal.gif",
#                "../../static.skyrock.net/img/loader/wait-horizontal.gif")