# import requests
# import threading
# import queue
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse, urljoin


# def crawl(max_pages=50):
#     internal_links = set()
#     subdomain_links = set()
#     external_links = set()
#     document_links = set()
#     broken_links = set()
#     visited_links = set()

#     def worker():
#         while True:
#             url = q.get()
#             if url in visited_links or len(visited_links) >= max_pages:
#                 q.task_done()
#                 continue
#             visited_links.add(url)
#             try:
#                 response = requests.get(url)
#             except:
#                 broken_links.add(url)
#                 q.task_done()
#                 continue
#             soup = BeautifulSoup(response.text, "lxml")
#             for a_tag in soup.find_all("a", href=True):
#                 href = a_tag.get("href")
#                 if href and not href.startswith("#"):
#                     joined_link = urljoin(url, href)
#                     parsed_link = urlparse(joined_link)
#                     if parsed_link.scheme not in ["http", "https"]:
#                         continue
#                     if parsed_link.fragment:
#                         joined_link = joined_link.split("#")[0]
#                         parsed_link = urlparse(joined_link)
#                     if is_internal(parsed_link):
#                         if is_subdomain(parsed_link):
#                             subdomain_links.add(joined_link)
#                         else:
#                             internal_links.add(joined_link)
#                         if len(visited_links) < max_pages:
#                             q.put(joined_link)
#                     elif is_external(parsed_link):
#                         external_links.add(joined_link)
#                     else:
#                         continue
#                 elif href and href.endswith((".doc", ".docx", ".pdf")):
#                     document_links.add(urljoin(url, href))
#             q.task_done()

#     def is_internal(parsed_link):
#         return not parsed_link.netloc or parsed_link.netloc == root_netloc

#     def is_subdomain(parsed_link):
#         return parsed_link.hostname.endswith(root_netloc)

#     def is_external(parsed_link):
#         return parsed_link.netloc and not is_subdomain(parsed_link)

#     url = input("Enter a URL to crawl:")
#     parsed_url = urlparse(url)
#     root_netloc = parsed_url.hostname

#     q = queue.Queue()
#     q.put(url)

#     for i in range(20):
#         t = threading.Thread(target=worker)
#         t.daemon = True
#         t.start()

#     q.join()

#     print(f"Internal Links ({len(internal_links)}):\n{internal_links}")
#     print(f"Subdomain Links ({len(subdomain_links)}):\n{subdomain_links}")
#     print(f"External Links ({len(external_links)}):\n{external_links}")
#     print(f"Document Links ({len(document_links)}):\n{document_links}")
#     print(f"Broken Links ({len(broken_links)}):\n{broken_links}")


# crawl()


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

seed_url = "https://msu.ru"  # ... your seed URL here
max_visits = 10000  # ... max number of pages to visit
num_workers = 5  # ... number of workers to run in parallel

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

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")

    except (requests.exceptions.RequestException, UnicodeError):
        print(f"{RED}[*] Broken link: {url}{RESET}")
        broken_urls.add(url)
        return internal_links, subdomain_links, external_links, document_links, broken_urls

    # get internal and subdomain links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        if is_skip_link(href):
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
        if is_skip_link(href):
            continue
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
            continue
        elif href.endswith(".doc") or href.endswith(".docx") or href.endswith(".pdf") or href.endswith(".xls") or href.endswith(".xlsx"):
            print(f"{PURPLE}[*] Document link: {href}{RESET}")
            document_links.add(href)
            continue
        else:
            joined_link = urljoin(url, href)
            parsed_link = urlparse(joined_link)
            if is_valid(joined_link) and parsed_link.netloc != parsed.netloc and not parsed_link.netloc.endswith(parsed.netloc):
                print(f"{GRAY}[*] External link: {joined_link}{RESET}")
                external_links.add(joined_link)

    # # get document links
    # for a_tag in soup.find_all("a", href=True):
    #     href = a_tag.get("href")
    #     if is_skip_link(href):
    #         continue
    #     if href.endswith(".doc") or href.endswith(".docx") or href.endswith(".pdf") or href.endswith(".xls") or href.endswith(".xlsx"):
    #         print(f"{PURPLE}[*] Document link: {href}{RESET}")
    #         document_links.add(href)
    #         continue

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
    result = get_links(url)

    if len(result) < 4:
        # Handle the case where get_links() returns less than four values
        internal_links, subdomain_links, external_links, document_links = set(), set(), set(), set()
    else:
        internal_links, subdomain_links, external_links, document_links = result

    for link in internal_links | subdomain_links:
        if link not in visited:
            q.put(link)

    internal_urls.update(internal_links)
    subdomains.update(subdomain_links)
    external_urls.update(external_links)
    document_urls.update(document_links)


# def extract_content(url):
#     internal_links, subdomain_links, document_links, external_links = get_links(
#         url)

#     for link in internal_links | subdomain_links:
#         if link not in visited:
#             q.put(link)

#     internal_urls.update(internal_links)
#     subdomains.update(subdomain_links)
#     external_urls.update(external_links)
#     document_urls.update(document_links)

# def extract_content(url):
#     internal_links, subdomain_links, external_links, document_links = get_links(
#         url)
#     internal_urls.update(internal_links)
#     subdomains.update(subdomain_links)
#     external_urls.update(external_links)
#     document_links.update(document_links)

#     for link in internal_links | subdomain_links:
#         if link not in visited:
#             q.put(link)

# crawl the internal links and subdomain links


def crawl(url):
    visited.add(url)
    # print("Crawl: ", url)
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    extract_content(url)
    for link in subdomains.union(internal_urls):
        if link not in visited:
            q.put(link)

# worker thread


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
print("[+] Total links:", len(internal_urls) + len(external_urls) +
      len(subdomains) + len(broken_urls) + len(document_urls))


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
