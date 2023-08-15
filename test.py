import re
import logging

from dataclasses import asdict

from skydump import parse_page, find_mimetype
from skydump import parse_url, crawl_page, open_resource_manifest, get_resource_local_url
from skydump import download


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


START_URL = "https://pips.skyrock.com"

ALLOW_CRAWL_CONDITIONS = [
    re.compile(r"[a-zA-Z0-9\-]+\.skyrock\.com", re.I),
]

FORBID_CRAWL_CONDITIONS = [
    re.compile(r"(?:" + "|".join(BLACKLIST_SUBDOMAINS) + r")\.skyrock\.com", re.I),
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


page = crawl_page(START_URL, ALLOW_CRAWL_CONDITIONS, FORBID_CRAWL_CONDITIONS)
print(page)

#download("https://pips.skyrock.com/", "test.html")