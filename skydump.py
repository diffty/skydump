import requests
import re
import os
import logging
import shutil
import mimetypes
from dataclasses import dataclass, asdict
from typing import List, Set

from bs4 import BeautifulSoup, PageElement, Tag

from models.link import Link, LinkType
from models.page import Page


REG_DOMAIN = re.compile(r"([a-zA-Z]*://[^\/]+)", re.I)
REG_SUBDOMAIN = re.compile(r"(?:[a-zA-Z]*://)?([a-zA-Z0-9\-\.]+)", re.I)
REG_BLOG = re.compile(r"([a-zA-Z0-9\-]+)\.skyrock\.com", re.I)
REG_PAGE = re.compile(r"/(\d+)\.html", re.I)
REG_RESOURCE_OLD = re.compile(r'"((?:[a-zA-Z]*://)?[^ "]+)"', re.I)
REG_RESOURCE = re.compile(r'((?:[a-zA-Z]*:\/)?\/.+)', re.I)
REG_URL_NO_PROTOCOL = re.compile(r"^(?:[a-zA-Z]*://)?(.+)", re.I)


def parse_page(url,
               allow_crawl_conditions: List[re.Pattern] = list(),
               forbid_crawl_conditions: List[re.Pattern] = list()):
    """
    Downloads a page, parse it, returns a list of Link objects extracted from
    what as been found in the Page

    url: page to parse
    allow_crawl_conditions: list of regexes that must match to allow the link to be entered
    forbid_crawl_conditions: list of regexes that must NOT match to allow the link to be entered
    """
    
    domain_reg = REG_DOMAIN.search(url)
    if not domain_reg:
        raise Exception("Can't parse domain in url {url}")

    curr_page = Page(remote_url=url, domain=domain_reg.group(1))

    logging.info(f"Requesting page {url}")

    response = requests.get(url)
    if response:
        html_doc = response.text

        soup = BeautifulSoup(html_doc, 'html.parser')
        link_attr_list = ["src", "href"]  # "content"

        def _predicate(t: Tag):
            return any(map(t.has_attr, link_attr_list))

        url_list: List[Tag] = soup.find_all(_predicate)
        for u in url_list:
            new_link = Link()
            new_link.origin = url

            if u.name == "a":
                link_str = u.get("href")

                logging.info(f"Found link {link_str}")

                new_link.type = LinkType.PAGE
                new_link.original_url = link_str

                if link_str.startswith("/"):
                    new_link.remote_url = curr_page.domain + link_str
                
                elif all(map(lambda r: r.search(link_str) is not None, allow_crawl_conditions)) and all(map(lambda r: r.search(link_str) is None, forbid_crawl_conditions)):
                    new_link.remote_url = link_str
                    
                else:
                    logging.info(f"Ignored link {link_str}")
                    continue
            
            else:
                for attr in link_attr_list:
                    link_str = u.get(attr)
                    
                    if link_str and REG_RESOURCE.match(link_str) and not link_str.startswith("//"):
                        if link_str.startswith("/"):
                            link_str = url + link_str
                        
                        logging.info(f"Found resource {link_str}")

                        new_link.type = LinkType.RESOURCE
                        new_link.original_url = link_str
                        new_link.remote_url = link_str

            if new_link.remote_url:
                curr_page.links.append(new_link)
    
        return curr_page
    
    return None


def parse_url(url):
    """
    Parse any url and return a list with the base path to the resource (without protocol)
    then the name of the resource.

    eg. parse_url("https://i.skyrock.net/778/417/pics/photo_417_small.jpg")
    => (['i.skyrock.net', '778', '417', 'pics'], 'photo_417_small.jpg')

    url: url to parse
    """

    res = REG_URL_NO_PROTOCOL.search(url)
    if not res:
        logging.warning(f"Can't download page {url}: non conform URL ")
        return None

    no_protocol_url = res.group(1)

    while no_protocol_url.endswith("/"):
        no_protocol_url = no_protocol_url[:-1]

    splitted_path = no_protocol_url.split("/")

    print(f"{splitted_path=}")

    if len(splitted_path) == 1:
        page_name = "index.html"
        page_path = splitted_path
    else:
        page_name = re.subn(r"[\\/:*?\"<>|]", "__", splitted_path[-1])
        page_name = page_name[0]

        #if os.path.splitext(page_name)[1].lower() not in [".htm", ".html"]:
        #    page_name += ".html"

        page_path = splitted_path[:-1]

    return page_path, page_name


def download_page(url, destination_path):
    logging.info(f"Downloading {url} to {destination_path}")

    r = requests.get(url)
    page_content = r.content

    if r.status_code != 200:
        logging.error(f"Error code {r.status_code} while getting page {url}")
        return None
    
    content_type = r.headers["Content-Type"]
    extension = mimetypes.guess_extension(r.headers["Content-Type"])

    if extension:
        destination_path = os.path.splitext(destination_path)[0] + extension
        
    with open(destination_path, "wb") as fp:
        if r.apparent_encoding:
            fp.write(page_content.decode(r.apparent_encoding).encode("utf-8"))
        else:
            fp.write(page_content)
    
    return destination_path, content_type


def remap_html_page(origin_local_url, original_url, local_url):
    logging.info(f"Remapping file {origin_local_url} by replacing {original_url} with {local_url}")

    local_file_content = None
    with open(origin_local_url, "rb") as fp:
        local_file_content = fp.read().decode("utf-8")

    with open(origin_local_url, "wb") as fp:
        fp.write(local_file_content.replace(f'"{original_url}"', local_url).encode("utf-8"))


post_process_link_resource_by_extension = {
    "css": [

    ]
}

post_process_page_by_extension = {
    "html": [
        lambda p, l: remap_html_page(p.local_url, l.remote_url, l.local_url)
    ],
}

def execute(url,
            allow_crawl_conditions: List[re.Pattern] = list(),
            forbid_crawl_conditions: List[re.Pattern] = list()):

    # Retrieve page and its allowed linked pages & resources
    page = parse_page(url, allow_crawl_conditions, forbid_crawl_conditions)

    for l in page.links:
        page_path, page_name = parse_url(l.remote_url)

        path = "/".join(page_path)

        if not os.path.exists(path):
            os.makedirs(path)
        
        destination_path = path + "/" + page_name
        print(f"{destination_path=}")
        downloaded_file, content_type = download_page(l.remote_url, destination_path)

        l.local_url = downloaded_file
        l.content_type = content_type

        # Backing up original page
        if l.type == LinkType.PAGE:
            shutil.copyfile(downloaded_file, downloaded_file + ".orig")
        

    # Remap page links & resources to local equivalents
    origin_local_page_path, origin_local_page_name = parse_url(url)
    origin_local_url = "".join(origin_local_page_path) + "/" + origin_local_page_name

    for l in page.links:
        parsed_local_url = l.local_url.split("/")

        if origin_local_page_path[0] != parsed_local_url[0]:
            relative_local_url = "../" * len(origin_local_page_path) + l.local_url

        else:
            for f in origin_local_page_path:
                if parsed_local_url[0] == f:
                    parsed_local_url = parsed_local_url[1:]
                else:
                    break

            relative_local_url = "/".join(parsed_local_url)
        
        remap_page(origin_local_url, l.original_url, relative_local_url)
