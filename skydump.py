import requests
import re
import os
import logging
import shutil
import mimetypes
import json
import html
from dataclasses import dataclass, asdict, replace
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


def parse_page(page: Page,
               allow_crawl_conditions: List[re.Pattern] = list(),
               forbid_crawl_conditions: List[re.Pattern] = list()):
    """
    Downloads a page, parse it, returns a list of Link objects extracted from
    what as been found in the Page

    url: page to parse
    allow_crawl_conditions: list of regexes that must match to allow the link to be entered
    forbid_crawl_conditions: list of regexes that must NOT match to allow the link to be entered
    """
    
    url = page.remote_url
    logging.info(f"Requesting page {url}")

    response = requests.get(url)
    if response:
        html_doc = response.text

        soup = BeautifulSoup(html_doc, 'html.parser')
        link_attr_list = ["src", "href"]  # "content"

        def _predicate(t: Tag):
            return any(map(t.has_attr, link_attr_list))
        
        discovered_link_urls = []

        url_list: List[Tag] = soup.find_all(_predicate)
        for u in url_list:
            new_link = Link()
            new_link.origin = url

            if u.name == "a":
                link_str = u.get("href")

                discovered_link_urls.append(link_str)

                logging.info(f"Found link {link_str}")

                url_reg = REG_URL_NO_PROTOCOL.search(link_str)
                if not url_reg:
                    raise Exception(f"Can't parse resource url: {link_str}")
                
                new_link.resource = Page()
                new_link.original_url = link_str

                new_link.resource.remote_url = link_str
                new_link.resource.protocol = url_reg.group(1)
                new_link.resource.domain = url_reg.group(2)

                if link_str.startswith("/"):
                    new_link.resource.remote_url = page.protocol + page.domain + link_str
                    new_link.resource.protocol = page.protocol
                    new_link.resource.domain = page.domain
                
                elif all(map(lambda r: r.search(link_str) is not None, allow_crawl_conditions)) and all(map(lambda r: r.search(link_str) is None, forbid_crawl_conditions)):
                    new_link.resource.remote_url = link_str
                    
                else:
                    logging.info(f"Ignored link {link_str}")
                    continue
            
            else:
                for attr in link_attr_list:
                    link_str = u.get(attr)
                    
                    if link_str and REG_RESOURCE.match(link_str) and not link_str.startswith("//"):
                        discovered_link_urls.append(link_str)

                        new_link.resource = Resource()
                        new_link.original_url = link_str

                        if link_str.startswith("/"):
                            link_str = url + link_str
                        
                        logging.info(f"Found resource {link_str}")

                        url_reg = REG_URL_NO_PROTOCOL.search(link_str)
                        if not url_reg:
                            raise Exception(f"Can't parse resource url: {link_str}")

                        new_link.resource.remote_url = link_str
                        new_link.resource.protocol=url_reg.group(1)
                        new_link.resource.domain=url_reg.group(2)

            if new_link.resource \
                and new_link.resource.remote_url:
                
                page.links.append(new_link)
    
    return page


def parse_url(url, add_extension=None):
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
        if add_extension is not None:
            page_name += add_extension
    
    page_path = [res.group(2)] + page_path
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
        return destination_path, None, None, r.status_code
    
    content_type = find_mimetype(r.headers["Content-Type"])
    content_encoding = r.apparent_encoding
    extension = mimetypes.guess_extension(content_type)

    if extension and os.path.splitext(destination_path)[1].lower() != extension:
        destination_path = destination_path + extension
    
    if overwrite is False and os.path.exists(destination_path):
        logging.info(f"Resource {destination_path} already exist. Skipping download!")
    else:
        with open(destination_path, "wb") as fp:
            if content_encoding:
                try:
                    fp.write(rsc_content.decode(content_encoding).encode(content_encoding))
                except UnicodeDecodeError as err:
                    fp.write(rsc_content)
                    content_encoding = None
            else:
                fp.write(rsc_content)
    
    return destination_path, content_type, content_encoding, r.status_code


def remap_html_page(origin_local_url, original_url, local_url, relative=True):
    if relative:
        local_url = (len(origin_local_url.split("/"))-1) * "../" + local_url

    logging.info(f"Remapping file {origin_local_url} by replacing {original_url} with {local_url}")

    local_file_content = None
    with open(origin_local_url, "rb") as fp:
        local_file_content = fp.read().decode("ISO-8859-1")

    with open(origin_local_url, "wb") as fp:
        fp.write(local_file_content.replace(f'"{html.escape(original_url)}"', f'"{html.escape(local_url)}"').encode("ISO-8859-1"))


PAGE_POST_PROCESSORS = [
    lambda p, l: remap_html_page(p.local_url, l.original_url, l.resource.local_url, relative=True)
]

ASSET_POST_PROCESSORS = {
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

    downloaded_file_path, content_type, encoding, return_code = download(remote_url, destination_path, overwrite)
    return downloaded_file_path, content_type, encoding, return_code


def open_resource_manifest(path: str):
    if os.path.exists(path):
        logging.info(f"Found resource manifest in {path}")

        with open(path, "r") as fp:
            rsc_json = json.load(fp)
            if rsc_json.get("type", None) == "page":
                return Page.load(rsc_json)
            else:
                return Resource.load(rsc_json)


def write_resource_manifest(rsc: Resource, path: str = None):
    if path is None:
        path = os.path.dirname(rsc.local_url) + "/" + os.path.basename(get_resource_local_url(rsc.remote_url)) + ".json"
    
    logging.info(f"Writing resource {rsc.remote_url} manifest in {path}")

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, "w") as fp:
        fp.write(json.dumps(asdict(rsc), indent=4))


def crawl_page(url,
               allow_crawl_conditions: List[re.Pattern] = list(),
               forbid_crawl_conditions: List[re.Pattern] = list()):
    
    page_local_url = get_resource_local_url(url)
    page = open_resource_manifest(page_local_url + ".json")

    if page is None:
        domain_reg = REG_URL_NO_PROTOCOL.search(url)
        if not domain_reg:
            raise Exception(f"Can't parse url: {url}")

        page = Page(remote_url=url, domain=domain_reg.group(2), protocol=domain_reg.group(1))

    if not page.complete:
        # Retrieve page and its allowed linked pages & resources
        page = parse_page(page, allow_crawl_conditions, forbid_crawl_conditions)
        page.local_url = get_resource_local_url(page.remote_url)

        # Write first manifest with first infos we do have rn
        write_resource_manifest(page)

        # Actually download the page then update the manifest with the real local filepath & info
        downloaded_file_path, content_type, encoding, return_code = retrieve_resource(page.remote_url, page.local_url)
        page.content_type = content_type
        page.local_url = downloaded_file_path
        page.content_encoding = encoding
        page.return_code = return_code

        write_resource_manifest(page)

        # Backing up original page
        backup_path = downloaded_file_path + ".orig"
        if not os.path.exists(backup_path) and os.path.exists(downloaded_file_path):
            shutil.copyfile(downloaded_file_path, backup_path)

    for l in page.links:
        local_url = get_resource_local_url(l.resource.remote_url)
        rsc = open_resource_manifest(local_url + ".json")

        if rsc and os.path.exists(rsc.local_url):
            l.resource = rsc
        else:
            l.resource.local_url = local_url

            downloaded_file_path, content_type, encoding, return_code = retrieve_resource(l.resource.remote_url,
                                                                        local_url,
                                                                        overwrite=False)
            
            # Updating the local_url field with the real local url of thed ownloaded file
            # (to integrate corrected extension detected from the mimetype)
            l.resource.local_url = downloaded_file_path
            l.resource.content_type = content_type
            l.resource.content_encoding = encoding
            l.resource.return_code = return_code

            # If we just downloaded an html page (badly detected because it was not in a <a> link),
            # We upgrade it as a Page
            if content_type == "text/html":
                l.resource = Page(**asdict(l.resource))
                l.resource.type = "page"

            write_resource_manifest(l.resource)

    # Run post-process operations
    if not page.complete:
        for link in page.links:
            for fn in PAGE_POST_PROCESSORS:
                fn(page, link)

        for link in page.links:
            fn_list = ASSET_POST_PROCESSORS.get(link.resource.content_type, [])
            for fn in fn_list:
                fn(page, link)

        page.complete = True

        # Hardcode strip of linked pages links to avoid filling manifests with nested pages
        for l in page.links:
            if isinstance(l.resource, Page):
                l.resource.links = []

        write_resource_manifest(page)

    return page


#TODO: retirer les links dans le manifest parce que sinon ça fait des json impbriqués de l'enfer
