from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import queue
from threading import Thread
import os
import colorama
import re
from concurrent.futures import ThreadPoolExecutor

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW
PURPLE = colorama.Fore.MAGENTA
RED = colorama.Fore.RED
BLUE = colorama.Fore.BLUE
CREAM = colorama.Fore.LIGHTYELLOW_EX
ORANGE = colorama.Fore.LIGHTRED_EX
MEROON = colorama.Fore.LIGHTMAGENTA_EX
CYAN = colorama.Fore.CYAN

seed_url = "https://spbu.ru"  # ... your seed URL here
max_visits = 1000  # ... max number of pages to visit
num_workers = 20  # ... number of workers to run in parallel

visited = set()
internal_urls = set()
external_urls = set()
subdomains = set()
broken_urls = set()
document_urls = set()


def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)



def is_skip_link(link):
    skip_link_types = ['mailto:', 'tel:', '.jpg', '.jpeg', '.png', '.gif',
                       '.svg', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.ogg', '.webm']
    for skip_type in skip_link_types:
        if link.startswith(skip_type):
            return True
    return False


def extract_links(url, soup):
    parsed = urlparse(url)
    # get the links you want to follow here
    return [a.get("href")
            for a in soup.find_all("a")
            if a.get("href") and is_valid(a.get("href")) and urlparse(a.get("href")).netloc == parsed.netloc and not is_skip_link(a.get("href"))]


def get_links(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    parsed = urlparse(url)
    internal_links = set()
    subdomain_links = set()
    external_links = set()
    document_links = set()

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    # get internal and subdomain links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        elif href.startswith("#"):
            internal_links.add(href)

        else:
            joined_link = urljoin(url, href)
            parsed_link = urlparse(joined_link)
            if is_valid(joined_link) and parsed_link.netloc == parsed.netloc:
                print(f"{GREEN}[*] Internal link: {joined_link}{RESET}")
                internal_links.add(joined_link)
            elif is_valid(joined_link) and parsed_link.netloc != parsed.netloc and parsed_link.netloc.endswith(parsed.netloc):
                print(f"{BLUE}[*] Subdomain link: {joined_link}{RESET}")
                subdomain_links.add(joined_link)

    # get external links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        else:
            joined_link = urljoin(url, href)
            parsed_link = urlparse(joined_link)
            if is_valid(joined_link) and parsed_link.netloc != parsed.netloc and not parsed_link.netloc.endswith(parsed.netloc):
                print(f"{GRAY}[*] External link: {joined_link}{RESET}")
                external_links.add(joined_link)

    # get document links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if href.endswith(".doc") or href.endswith(".docx") or href.endswith(".pdf") or href.endswith(".xls") or href.endswith(".xlsx"):
            print(f"{PURPLE}[*] Document link: {href}{RESET}")
            document_links.add(href)
            

    return internal_links, subdomain_links, external_links, document_links

def get_broken_links(url):
    internal_links, subdomain_links, external_links, document_links = get_links(
        url)
    all_links = internal_links | subdomain_links | external_links | document_links
    broken_urls = []

    def validate_url(url):
        response = requests.head(url)
        if response.status_code == 404:
            print(f"{RED}[*] Broken link: {url}{RESET}")
            broken_urls.append(url)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(validate_url, all_links)

    return broken_urls


def extract_content(url):
    internal_links, subdomain_links, external_links, document_links = get_links(
        url)
    internal_urls.update(internal_links)
    subdomains.update(subdomain_links)
    external_urls.update(external_links)
    document_urls.update(document_links)

    for link in internal_links:
        if link not in visited:
            q.put(link)

# crawl the internal links and subdomain links
def crawl(url):
    visited.add(url)
    # print("Crawl: ", url)
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    extract_content(url)
    for link in subdomains.union(internal_urls):
        if link not in visited:
            q.put(link)

#worker thread
def queue_worker(i, q):
    while True:
        url = q.get()
        if len(visited) < max_visits and url not in visited:
            crawl(url)
        q.task_done()


q = queue.Queue()
for i in range(num_workers):
    Thread(target=queue_worker, args=(i, q), daemon=True).start()

q.put(seed_url)
q.join()

# print the results
print("[+] Total visited links:", len(visited))
print("[+] Total Internal links:", len(internal_urls))
print("[+] Total External links:", len(external_urls))
print("[+] Total Subdomains links:", len(subdomains))
print("[+] Total Broken links:", len(broken_urls))
print("[+] Total Document links:", len(document_urls))
print("[+] Total links:", len(internal_urls) + len(external_urls) + len(subdomains) + len(broken_urls) + len(document_urls))


# create folder for the website
domain = urlparse(seed_url).netloc
folder = f"./{domain}"
if not os.path.exists(folder):
    os.makedirs(folder)


with open(f"{folder}/visited.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(visited))


with open(f"{folder}/internal_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(internal_urls))

with open(f"{folder}/external_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(external_urls))

with open(f"{folder}/subdomains.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(subdomains))

with open(f"{folder}/broken_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(broken_urls))

with open(f"{folder}/document_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(document_urls))

