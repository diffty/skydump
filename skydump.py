import requests
import re
import os
import logging
import shutil
import mimetypes
import json
from dataclasses import dataclass, asdict
from typing import List, Set

from bs4 import BeautifulSoup, PageElement, Tag

from models.link import Link
from models.page import Page
from models.resource import Resource


REG_DOMAIN = re.compile(r"([a-zA-Z]*://[^\/]+)", re.I)
REG_SUBDOMAIN = re.compile(r"(?:[a-zA-Z]*://)?([a-zA-Z0-9\-\.]+)", re.I)
REG_BLOG = re.compile(r"([a-zA-Z0-9\-]+)\.skyrock\.com", re.I)
REG_PAGE = re.compile(r"/(\d+)\.html", re.I)
REG_RESOURCE_OLD = re.compile(r'"((?:[a-zA-Z]*://)?[^ "]+)"', re.I)
REG_RESOURCE = re.compile(r'((?:[a-zA-Z]*:\/)?\/.+)', re.I)
REG_URL_NO_PROTOCOL = re.compile(r"^([a-zA-Z]+://)?([^\/]*)(\/[^?]*)?(\?.*)?", re.I)
#(.+)


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
    
    domain_reg = REG_URL_NO_PROTOCOL.search(url)
    if not domain_reg:
        raise Exception(f"Can't parse url: {url}")

    curr_page = Page(remote_url=url, domain=domain_reg.group(2), protocol=domain_reg.group(1))

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

                url_reg = REG_URL_NO_PROTOCOL.search(link_str)
                if not url_reg:
                    raise Exception(f"Can't parse resource url: {link_str}")
                
                new_link.resource = Page()
                new_link.original_url = link_str

                new_link.resource.remote_url = link_str
                new_link.resource.protocol=url_reg.group(1)
                new_link.resource.domain=url_reg.group(2)

                if link_str.startswith("/"):
                    new_link.resource.remote_url = curr_page.protocol + curr_page.domain + link_str
                    new_link.resource.protocol = curr_page.protocol
                    new_link.resource.domain = curr_page.domain
                
                elif all(map(lambda r: r.search(link_str) is not None, allow_crawl_conditions)) and all(map(lambda r: r.search(link_str) is None, forbid_crawl_conditions)):
                    new_link.resource.remote_url = link_str
                    
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

                        url_reg = REG_URL_NO_PROTOCOL.search(link_str)
                        if not url_reg:
                            raise Exception(f"Can't parse resource url: {link_str}")

                        new_link.resource = Resource()
                        new_link.original_url = link_str

                        new_link.resource.remote_url = link_str
                        new_link.resource.protocol=url_reg.group(1)
                        new_link.resource.domain=url_reg.group(2)

            if new_link.resource and new_link.resource.remote_url:
                curr_page.links.append(new_link)
    
        return curr_page
    
    return None


def parse_url(url, force_extension=None):
    """
    Parse any url and return a list with the base path to the resource (without protocol)
    then the name of the resource.

    eg. parse_url("https://i.skyrock.net/778/417/pics/photo_417_small.jpg")
    => (['i.skyrock.net', '778', '417', 'pics'], 'photo_417_small.jpg')

    url: url to parse
    add_html_extension: always add a .html to the name if the resource is not already a .htm/.html
    """

    res = REG_URL_NO_PROTOCOL.search(url)
    if not res:
        logging.warning(f"Can't download page {url}: non conform URL ")
        return None

    parameters = res.group(4)

    if res.group(3) is None:
        page_name = "index.html"
        page_path = []
    else:
        is_folder = res.group(3).endswith("/")

        no_protocol_url = res.group(3).lstrip("/")
        splitted_path = res.group(3).strip("/").split("/")

        #print(f"{no_protocol_url=}")
        #print(f"{splitted_path=}")

        if "/" not in no_protocol_url:
            page_name = no_protocol_url if no_protocol_url != "" else "index.html"
            page_path = []
        else:
            if is_folder:
                page_name = "index.html"
                page_path = splitted_path
            else:
                page_name = splitted_path[-1]
                page_path = splitted_path[:-1]

        if parameters:
            escaped_parameters = re.subn(r"[\\/:*?\"<>|]", "_", parameters)
            page_name = page_name + escaped_parameters[0]

        # TODO: somehow vérifier le ContentType avant de faire ça
        if force_extension is not None:
            page_name += force_extension
    
    page_path = [res.group(2)] + page_path

    #print(f"{page_path=}, {page_name=}")
    #print(f"{res.group(2)}/{'/'.join(page_path)}/{page_name}")
    #print()

    return page_path, page_name


def find_mimetype(header_content_type: str) -> str:
    res = re.search(r"([^/;]+/[^/;]+)", header_content_type)
    if res:
        return res.group(1).strip()
    else:
        logging.error(f"Haven't find mimetype for Content-Type {header_content_type}")
        return None


def download(url, destination_path, overwrite=True):
    logging.info(f"Downloading {url} to {destination_path}")

    r = requests.get(url)
    rsc_content = r.content

    if r.status_code != 200:
        logging.error(f"Error code {r.status_code} while getting resource {url}.")
        return None
    
    content_type = find_mimetype(r.headers["Content-Type"])
    extension = mimetypes.guess_extension(content_type)

    if extension:
        destination_path = os.path.splitext(destination_path)[0] + extension
    
    if overwrite is False and os.path.exists(destination_path):
        logging.info(f"Resource {destination_path} already exist. Skipping download!")
    else:
        with open(destination_path, "wb") as fp:
            if r.apparent_encoding:
                fp.write(rsc_content.decode(r.apparent_encoding).encode("utf-8"))
            else:
                fp.write(rsc_content)
    
    return destination_path, content_type


def remap_html_page(origin_local_url, original_url, local_url, relative=True):
    if relative:
        local_url = (len(origin_local_url.split("/"))-1) * "../" + local_url

    logging.info(f"Remapping file {origin_local_url} by replacing {original_url} with {local_url}")

    local_file_content = None
    with open(origin_local_url, "rb") as fp:
        local_file_content = fp.read().decode("utf-8")

    with open(origin_local_url, "wb") as fp:
        fp.write(local_file_content.replace(f'"{original_url}"', local_url).encode("utf-8"))


page_post_processors = [
    lambda p, l: remap_html_page(p.local_url, l.resource.remote_url, l.resource.local_url, relative=True)
]

asset_post_processors = {
    "text/css": [
        
    ]
}


def get_resource_local_url(remote_url):
    rsc_path, rsc_name = parse_url(remote_url)
    return "/".join(rsc_path) + "/" + rsc_name


def retrieve_resource(remote_url, destination_path, overwrite=True):
    destination_dir = os.path.dirname(destination_path)

    if destination_dir != "" and not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    downloaded_file, content_type = download(remote_url, destination_path, overwrite)
    return downloaded_file, content_type


def write_resource_manifest(rsc: Resource, path: str = None):
    if path is None:
        path = os.path.splitext(rsc.local_url)[0] + ".json"
    
    logging.info(f"Writing resource {rsc.remote_url} manifest in {path}")

    with open(path, "w") as fp:
        fp.write(json.dumps(asdict(rsc), indent=4))


# TODO: POUR REGLER PROBLMEE DE DEVOIR DL LE FICHIER POUR AVOIR SON MIME
# ON LE DL LA PREMIERE FOIS ET ON CREE UN JSON A COTE AVEC LE NOM DU TRUC BASIQUE + JSON QUI MAPPE
# LE vRAI FICHIER AVEC L'URL DE BASE ETC
def execute(url,
            allow_crawl_conditions: List[re.Pattern] = list(),
            forbid_crawl_conditions: List[re.Pattern] = list()):

    # Retrieve page and its allowed linked pages & resources
    page = parse_page(url, allow_crawl_conditions, forbid_crawl_conditions)
    
    page.local_url = get_resource_local_url(page.remote_url)
    downloaded_file, content_type = retrieve_resource(page.remote_url, page.local_url)
    page.content_type = content_type

    write_resource_manifest(page)

    # Backing up original page
    shutil.copyfile(downloaded_file, downloaded_file + ".orig")

    for l in page.links:
        destination_path = get_resource_local_url(l.resource.remote_url)
        l.resource.local_url = destination_path

        downloaded_file, content_type = retrieve_resource(l.resource.remote_url,
                                                          destination_path,
                                                          overwrite=False)
        
        # Updating the local_url field with the real local url of thed ownloaded file
        # (to integrate corrected extension detected from the mimetype)
        l.resource.local_url = downloaded_file
        l.resource.content_type = content_type

        write_resource_manifest(l.resource)

    # Run post-process operations
    for link in page.links:
        for fn in page_post_processors:
            fn(page, link)

    for link in page.links:
        fn_list = asset_post_processors.get(link.resource.content_type, [])
        for fn in fn_list:
            fn(page, link)

    # # Remap page links & resources to local equivalents
    # origin_local_page_path, origin_local_page_name = parse_url(url)
    # origin_local_url = "".join(origin_local_page_path) + "/" + origin_local_page_name

    # for l in page.links:
    #     parsed_local_url = l.local_url.split("/")

    #     if origin_local_page_path[0] != parsed_local_url[0]:
    #         relative_local_url = "../" * len(origin_local_page_path) + l.local_url

    #     else:
    #         for f in origin_local_page_path:
    #             if parsed_local_url[0] == f:
    #                 parsed_local_url = parsed_local_url[1:]
    #             else:
    #                 break

    #         relative_local_url = "/".join(parsed_local_url)
    #     
    #     remap_page(origin_local_url, l.original_url, relative_local_url)
