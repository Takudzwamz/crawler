import pytest
import os
from final_crawler import crawl, is_valid,  extract_content, get_links, is_skip_link, extract_links, queue_worker

# Do you tests here
import queue
from threading import Thread

# These test cases check the following:
# The url is invalid
# The queue_worker function correctly handles an empty queue.
# To run test, we run this on terminal: pytest zhang_pytest.py


# The url is invalid
def test_is_invalid():
   assert is_valid("http://spbu12345.ru") == True

# The url is invalid
# The queue_worker function correctly handles an empty queue.
def test_queue_worker_no_urls():
    # initialize variables
    global visited
    visited = set()
    global max_visits
    max_visits = 5
    num_workers = 2

    # initialize empty queue
    q = queue.Queue()

    # start worker threads
    for i in range(num_workers):
        Thread(target=queue_worker, args=(i, q), daemon=True).start()

    # wait for queue to empty
    q.join()

    # check if visited set is empty
    assert len(visited) == 0





