import pytest
import os
from final_crawler import crawl, is_valid,  extract_content, get_links, is_skip_link, extract_links, queue_worker, get_broken_links, q
import requests
from bs4 import BeautifulSoup
from queue import Queue
import threading
# Do you tests here

seed_url = "https://msu.ru"  # ... your seed URL here

visited = set()
internal_urls = set()
external_urls = set()
subdomains = set()
broken_urls = set()
document_urls = set()


def test_is_valid():
   assert is_valid("http://spbu.ru") == True
   assert is_valid(seed_url) == True
   assert is_valid("https://www.google.com/logo.png") == True
   assert is_valid("https://www.youtube.com") == True
   assert is_valid("https://www.vk.com") == True
   assert is_valid("https://www.facebook.com") == True
   assert is_valid("https://www.instagram.com") == True


def test_is_skip_link():
   assert is_skip_link("mailto:john@example.com") == True
   assert is_skip_link("tel:0123456789") == True
   assert is_skip_link("https://www.google.com/logo.png") == False
   assert is_skip_link("#") == False
   assert is_skip_link("http://www.google.com") == False


def test_extract_links():
   response = requests.get(seed_url)
   soup = BeautifulSoup(response.content, "html.parser")
   links = extract_links(seed_url, soup)
   assert len(links) == 0
   assert all(isinstance(link, str) for link in links)
   assert all(link.startswith(seed_url) for link in links)
   assert all(link not in external_urls for link in links)  
   assert all(link not in subdomains for link in links)


def test_get_links():

   internal_links, subdomain_links, external_links, document_links = get_links(seed_url)
   assert len(internal_links) > 0
   assert all(isinstance(link, str) for link in internal_links)
   assert all(link.startswith(seed_url) for link in internal_links)
   assert all(link not in external_urls for link in internal_links)
   assert len(subdomain_links) >= 0
   assert all(isinstance(link, str) for link in subdomain_links)
   assert all(link not in internal_urls for link in subdomain_links)
   assert all(link not in external_urls for link in subdomain_links)
   assert len(external_links) >= 0
   assert all(isinstance(link, str) for link in external_links)
   assert all(link not in internal_urls for link in external_links)
   assert all(link not in subdomains for link in external_links)
   assert len(document_links) >= 0
   assert all(isinstance(link, str) for link in document_links)
   assert all(link.endswith(".doc") or link.endswith(".docx") or link.endswith(".pdf") or link.endswith(".xls") or link.endswith(".xhtml") for link in document_links)


def test_get_broken_links():
   broken_urls = get_broken_links(seed_url)
   assert len(broken_urls) == 0
   assert all(isinstance(link, str) for link in broken_urls)



def test_extract_content():
   internal_links, subdomain_links, external_links, document_links = get_links(seed_url)
   internal_urls.update(internal_links)
   subdomains.update(subdomain_links)
   external_urls.update(external_links)
   document_urls.update(document_links)


   for link in internal_links:
       if link not in visited:
           q.put(link)

   assert q.qsize() > 0
   assert all(isinstance(link, str) for link in internal_links)
   assert all(link.startswith(seed_url) for link in internal_links)


def test_crawl():
   crawl(seed_url)
   assert q.qsize() > len(internal_urls) 
   assert len(visited) == 0
   assert len(internal_urls) > 0


def test_queue_worker():
    # Créer une file d'attente avec des liens factices pour tester
    test_q = Queue()
    test_q.put('https://vk.com')
    test_q.put('https://spbu.ru')
    test_q.put('https://msu.ru')
    
    # Initialiser les variables nécessaires pour la fonction queue_worker()
    visited = set()
    internal_urls = set()
    subdomains = set()
    external_urls = set()
    document_urls = set()
    max_visits = 3
    
    # Appeler la fonction queue_worker() avec les arguments nécessaires
    queue_worker(1, test_q, visited, internal_urls, subdomains, external_urls, document_urls, max_visits)
    
    # Vérifier que tous les liens ont été visités
    assert len(visited) == 3
    assert len(internal_urls) > 0

