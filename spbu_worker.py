import os
from bs4 import BeautifulSoup
import colorama
import requests
import requests.exceptions
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque
import asyncio


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
WHITE = colorama.Fore.WHITE

url = "https://spbu.ru"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


async def process_url(url, processed_urls, new_urls, total_urls_visited, broken_urls, document_urls, local_urls, subdomain_urls, foreign_urls):
    processed_urls.add(url)
    total_urls_visited += 1
    print(f"{YELLOW}[*] Now Crawling: {url}{RESET}")
    # try:
    #     response = await asyncio.get_event_loop().run_in_executor(None, requests.get, url)
    # except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
    #     print(f"{RED}[*] Broken link: {url}{RESET}")
    #     broken_urls.add(url)
    #     return
    retries = 0
    while True:
        try:
            response = await asyncio.get_event_loop().run_in_executor(None, requests.get, url)
            break
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema, requests.exceptions.RequestException,  Exception, requests.exceptions.Timeout, requests.exceptions.TooManyRedirects, requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.URLRequired) as e:
            if retries < 2:
                retries += 1
                print(
                    f"{RED}[*] Failed to fetch {url}: {e}. Retrying ({retries}/2)...{RESET}")
                await asyncio.sleep(1)
                continue
            else:
                print(f"{RED}[*] Broken link: {url}{RESET}")
                broken_urls.add(url)
                return

    parts = urlsplit(url)
    base = "{0.netloc}".format(parts)
    strip_base = '.'.join(base.split('.')[-2:])
    base_url = "{0.scheme}://{0.netloc}".format(parts)
    path = url[:url.rfind('/')+1] if '/' in parts.path else url

    # soup = BeautifulSoup(response.content , "lxml")
    # create a beutiful soup for the html document
    try:
        soup = BeautifulSoup(requests.get(
            url, headers=headers).content, "lxml")
    except Exception as e:
        print(f"Could not parse {url}: {e}")
        num_tries = 0
        while num_tries < 2:
            try:
                soup = BeautifulSoup(requests.get(
                    url, headers=headers).content, "lxml")
                break
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema, requests.exceptions.RequestException,  Exception, requests.exceptions.Timeout, requests.exceptions.TooManyRedirects, requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.URLRequired) as e:
                print(f"Could not fetch {url}: {e}")
                broken_urls.add(url)
                num_tries += 1
                continue
        # else:
        #     broken_urls.add(url)
        #     return
    # print(soup.prettify())
    
    for link in soup.find_all('a'):
        anchor = link.attrs["href"] if "href" in link.attrs else ''

        if anchor.startswith('mailto:') or anchor.startswith('tel:') or anchor.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.mp4', '.avi', '.mov')):
            continue
        elif anchor.endswith(('.doc', '.docx', '.pdf', '.pptx', '.ppt', '.xls', '.xlsx', '.csv', '.txt', '.rtf', '.zip', '.rar')):
            print(f"{MEROON}[*] Document link: {anchor}{RESET}")
            document_urls.add(anchor)
            continue
        elif anchor.startswith('/'):
            local_link = base_url + anchor
            print(f"{GREEN}[*] Local link: {local_link}{RESET}")
            local_urls.add(local_link)
        elif strip_base in anchor or base in anchor:
            parsed = urlparse(anchor)
            if parsed.netloc == base or parsed.netloc == strip_base:
                local_link = parsed.scheme + '://' + parsed.netloc + parsed.path
                if parsed.query:
                    local_link += '?' + parsed.query
                if parsed.fragment:
                    local_link += '#' + parsed.fragment
                print(f"{GREEN}[*] Local link: {local_link}{RESET}")
                local_urls.add(local_link)
            else:
                subdomains = parsed.netloc.split('.')
                if len(subdomains) > 2 and subdomains[-2] == strip_base.split('.')[0] or (len(subdomains) > 3 and subdomains[-3] == strip_base.split('.')[0]):
                    subdomain_urls.add(anchor)
                    print(f"{BLUE}[*] Subdomain link: {anchor}{RESET}")
                else:
                    print(f"{GRAY}[*] Foreign link: {anchor}{RESET}")
                    foreign_urls.add(anchor)
        else:
            print(f"{GRAY}[*] Foreign link: {anchor}{RESET}")
            foreign_urls.add(anchor)

    for i in local_urls.union(subdomain_urls):
        if i not in new_urls and i not in processed_urls:
            print(f"{PURPLE}[*] Adding to queue: {i}{RESET}")
            new_urls.append(i)



async def process_urls(new_urls, max_visits):
    processed_urls = set()
    total_urls_visited = 0
    broken_urls = set()
    document_urls = set()
    local_urls = set()
    subdomain_urls = set()
    foreign_urls = set()

    while new_urls and total_urls_visited < max_visits:
        url = new_urls.popleft()
        await process_url(url, processed_urls, new_urls, total_urls_visited, broken_urls, document_urls, local_urls, subdomain_urls, foreign_urls)
        total_urls_visited += 1
        print(
            f"{WHITE}[+] Visited {total_urls_visited} out of {max_visits} URLs")
        if total_urls_visited >= max_visits:
            break

    return (processed_urls, broken_urls, document_urls, local_urls, subdomain_urls, foreign_urls)




if __name__ == "__main__":
    new_urls = deque([url])
    max_visits = 10000  # ... max number of pages to visit
    loop = asyncio.get_event_loop()
    try:
        processed_urls,broken_urls, document_urls, local_urls, subdomain_urls, foreign_urls = loop.run_until_complete(
            process_urls(new_urls, max_visits))
    finally:
        loop.close()
        
    # Total URLs found
    total_urls_visited = len(broken_urls) + len(document_urls) + len(local_urls) + len(subdomain_urls) + len(foreign_urls)   

    # create a report of all urls
    print("[+] Total Internal links:", len(local_urls))
    print("[+] Total Subdomain links:", len(subdomain_urls))
    print("[+] Total Foreign links:", len(foreign_urls))
    print("[+] Total Document links:", len(document_urls))
    print("[+] Total Broken links:", len(broken_urls))
    print("[+] Total URLs found:", total_urls_visited)
    print("[+] Total Processed URLs:", len(processed_urls))
    print("[+]Number of unprocessed links:", len(new_urls))

    # create a report of all urls
    # create folder for the website
domain = urlparse(url).netloc
folder = f"./{domain}"
if not os.path.exists(folder):
    os.makedirs(folder)
    
# save all urls to a file
with open(f"{folder}/total_urls_found.txt", "w", encoding='utf-8') as f:
    f.write(str(total_urls_visited))

# save all broken urls to a file
with open(f"{folder}/broken_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(broken_urls))
    
# save all document urls to a file
with open(f"{folder}/document_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(document_urls))

# save all local urls to a file
with open(f"{folder}/local_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(local_urls))
    
# save all subdomain urls to a file
with open(f"{folder}/subdomain_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(subdomain_urls))
    
# save all foreign urls to a file
with open(f"{folder}/foreign_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(foreign_urls))
    
# save all processed urls to a file
with open(f"{folder}/processed_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(processed_urls))
    
# save all unprocessed urls to a file
with open(f"{folder}/unprocessed_urls.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(new_urls))

