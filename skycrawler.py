import requests
import re
import os
import logging
import shutil
from dataclasses import dataclass

from bs4 import BeautifulSoup, PageElement, Tag


@dataclass
class Site:
    discovered_blogs = set()


@dataclass
class Blog:
    name = ""
    url = ""
    discovered_links = set()
    nb_pages = 1

# Le monde il dort là d'sus

BLACKLIST_SUBDOMAINS = [
    "www",
    "lequipe-skyrock",
    "music",
    "cine",
    "sport",
    "fr",
    "en",
]

# Le temps fera les choses


REG_SUBDOMAIN = re.compile(r"(?:[a-zA-Z]*://)?([a-zA-Z0-9\-\.]+)", re.I)
REG_BLOG = re.compile(r"([a-zA-Z0-9\-]+)\.skyrock\.com", re.I)
REG_PAGE = re.compile(r"/(\d+)\.html", re.I)
REG_RESOURCE_OLD = re.compile(r'"((?:[a-zA-Z]*://)?[^ "]+)"', re.I)
REG_RESOURCE = re.compile(r'((?:[a-zA-Z]*:\/)?\/.+)', re.I)
REG_URL_NO_PROTOCOL = re.compile(r"^(?:[a-zA-Z]*://)?(.+)", re.I)


url = "http://les-bancs-bleus.skyrock.com"


def parse_page(url):
    logging.info(f"Parsing page {url}")

    discovered_blogs = set()
    discovered_links = set()
    discovered_resources = set()

    r = REG_BLOG.search(url)
    if r:
        current_blog_username = r.group(1)
        nb_pages = 1

        logging.info(f"Requesting page {url}")

        response = requests.get(url)
        if response:
            html_doc = response.text

            r = REG_SUBDOMAIN.search(url)
            if r:
                current_subdomain = r.group(1)

                logging.info(f"Found subdomain {current_subdomain}")

                soup = BeautifulSoup(html_doc, 'html.parser')
                links = soup.find_all("a")

                for l in links:
                    link_str = l.get("href")

                    logging.info(f"Found link {link_str}")

                    r = REG_BLOG.search(link_str)
                    if r:
                        discovered_username = r.group(1)

                        if discovered_username == current_blog_username:
                            discovered_links.add(link_str)

                        elif discovered_username not in BLACKLIST_SUBDOMAINS:
                            logging.info(f"Found username {discovered_username}")
                            discovered_blogs.add(discovered_username)
                        
                        else:
                            logging.info(f"Skipped link {link_str}")

                    elif link_str.startswith("/"):
                        r = REG_PAGE.search(link_str)
                        if r:
                            page_num = int(r.group(1))
                            if page_num > nb_pages:
                                nb_pages = page_num

                        discovered_links.add(url + link_str)

                    else:
                        logging.info(f"Ignored link {link_str}")

                link_attr_list = ["src", "href"]  # "content"

                def _predicate(t: Tag):
                    return any(map(t.has_attr, link_attr_list))

                resources = soup.find_all(_predicate)
                for r in resources:
                    for attr in link_attr_list:
                        link = r.get(attr)
                        
                        if link and REG_RESOURCE.match(link) and not link.startswith("//"):
                            if link.startswith("/"):
                                link = url + link
                            
                            if link not in discovered_links:
                                print(link)
                                discovered_resources.add(link)
            
            #for i in REG_RESOURCE.finditer(html_doc):
            #    print(i)
        
        return discovered_blogs, discovered_links, discovered_resources, nb_pages
    
    return None


def parse_url(url):
    res = REG_URL_NO_PROTOCOL.search(url)
    if not res:
        logging.warning(f"Can't download page {url}: non conform URL ")
        return None

    no_protocol_url = res.group(1)

    while no_protocol_url.endswith("/"):
        no_protocol_url = no_protocol_url[:-1]

    splitted_path = no_protocol_url.split("/")

    if len(splitted_path) == 1:
        page_name = "index.html"
        page_path = splitted_path
    else:
        page_name = re.subn(r"[\\/:*?\"<>|]", "__", splitted_path[-1])
        page_name = page_name[0]

        if os.path.splitext(page_name)[1].lower() not in [".htm", ".html"]:
            page_name += ".html"

        page_path = splitted_path[:-1]

    return page_path, page_name


def download_page(url, destination_path):
    r = requests.get(url)
    page_content = r.content

    if r.status_code != 200:
        logging.error(f"Error code {r.status_code} while getting page {url}")
        return None
    
    with open(destination_path, "wb") as fp:
        fp.write(page_content)


def remap_page(url):
    pass


logging.getLogger().setLevel(logging.INFO)

discovered_blogs, discovered_links, discovered_ressources, nb_pages = parse_page(url)

for link_url in discovered_links:
    page_path, page_name = parse_url(link_url)

    path = "/".join(page_path)

    if not os.path.exists(path):
        os.makedirs(path)
    
    destination_path = path + "/" + page_name
    #download_page(link_url, destination_path)

    # Backing up original page
    shutil.copyfile(destination_path, destination_path + ".orig")

for rsc_url in discovered_ressources:
    rsc_path, rsc_name = parse_url(rsc_url)

    path = "/".join(rsc_path)

    if not os.path.exists(path):
        os.makedirs(path)
    
    destination_path = path + "/" + page_name
    #download_page(rsc_url, destination_path)


remap_page(url)
