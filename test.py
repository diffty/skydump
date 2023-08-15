import re
import logging

from dataclasses import asdict

from skydump import parse_page, find_mimetype
from skydump import parse_url, execute


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


START_URL = "https://les-bancs-bleus.skyrock.com"

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


#t = parse_url("/2.html")""
#t = parse_url("https://www.skyrock.com")
#t = parse_url("https://www.skyrock.com/")
#t = parse_url("https://www.skyrock.com/inxed.tmlh")
#t = parse_url("https://www.skyrock.com/blog")
#t = parse_url("https://www.skyrock.com/blog/")
#t = parse_url("https://www.skyrock.com/blog/test")
#t = parse_url("https://www.skyrock.com/blog/testent/")
#t = parse_url("https://www.skyrock.com/blog/E.re")
#t = parse_url("https://www.skyrock.com/blog/cybercop.php")
#t = parse_url("https://www.skyrock.com/blog/cybercop.php?id=41887727&url=https://lbb.skyrock.com/")
#t = parse_url("https://www.skyrock.com/blog/?id=41887727&url=https://lbb.skyrock.com/")
#t = parse_url("https://www.skyrock.com/?id=41887727&url=https://lbb.skyrock.com/")


#print(find_mimetype("application/vnd.openxmlformats-officedocument.presentationml.presentation"))
#print(find_mimetype("text/html; charset=UTF-8"))
#print(find_mimetype("yeeeeauotajzo\"3^é''éù ; text/html; charset=UTF-8"))

execute(START_URL, ALLOW_CRAWL_CONDITIONS, FORBID_CRAWL_CONDITIONS)
