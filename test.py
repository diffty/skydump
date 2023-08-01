import re
import logging

from dataclasses import asdict

from skydump import parse_page


BLACKLIST_SUBDOMAINS = [
    "www",
    "lequipe-skyrock",
    "music",
    "cine",
    "sport",
    "fr",
    "en",
]


START_URL = ""
ALLOW_CRAWL_CONDITIONS = [
    re.compile(r"[a-zA-Z0-9\-]+\.skyrock\.com", re.I),
]

FORBID_CRAWL_CONDITIONS = [
    re.compile(r"(?:" + "|".join(BLACKLIST_SUBDOMAINS) + r")\.skyrock\.com", re.I),
]

page = parse_page(START_URL, ALLOW_CRAWL_CONDITIONS, FORBID_CRAWL_CONDITIONS)

print("==== LINKS ====")
for l in page.links:
    print("Remote URL:" + l.remote_url)
    print("Local URL:" + l.local_url)
    print("Origin:" + l.origin)
    print("Type:" + str(l.type))
    print()


from skydump2 import parse_url, execute
t = parse_url("https://www.skyrock.com/blog/cybercop.php?id=41887727&url=https://lbb.skyrock.com/")
t = parse_url("/2.html")
print(t)

logging.getLogger().setLevel(logging.INFO)

execute(START_URL, ALLOW_CRAWL_CONDITIONS, FORBID_CRAWL_CONDITIONS)
