import requests
import queue
from bs4 import BeautifulSoup, SoupStrainer
import multiprocessing as mp
from urllib.parse import urljoin
from functools import reduce
import time
import os
import sys
import re
from ctypes import c_long
from tldextract import extract

# searches for a file extension
is_file = re.compile('\.[^\/]*$')

try:
    THREADS = int(sys.argv[2])
except IndexError:
    THREADS = 25

# Have colorised output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Take in URL from cmd
root = sys.argv[1]
parsed_root = extract(root)
# Max queue size because reasons
# It dies if the queue fills up
# This could be considered a design flaw
urls_to_get = mp.Queue(32000)

# Put these in the queue when you've got bored
class Stop():
    pass


class Getter(mp.Process):
    """
    Multiprocessing object representing a single downloader and parser.
    Will retrieve URL from queue, download whatever is at that URL and attempt
    to mirror the file structure in the current working directory.

    Additionally, if the URL yields a HTML file, it will parse this file for
    hyperlinks to the same domain and adds those URLs to the queue for downloading
    later.
    """
    def __init__(self, queue, count, seen):
        super(Getter, self).__init__()
        self.queue = queue
        self.count = count
        self.seen = seen

    def run(self):
        # Run forever, until we recieve a Stop
        while True:
            url = self.queue.get()
            # Kill
            if type(url) == Stop:
                break
            # If we have a URL, tell the master process we're busy
            with self.count.get_lock():
                self.count.value += 1
            try:
                # Try and download the URL. If we can't, report and move on
                self._get_one(url)
            except Exception as e:
                print(bcolors.FAIL, e, bcolors.ENDC)
            finally:
                # Make sure we report we're done working
                with self.count.get_lock():
                    self.count.value -= 1

    def _put_url(self, url, link):
        """ If we haven't seen this URL before, add it to the queue """
        new_url = urljoin(url, link)
        new_url = new_url.split('#')[0]
        assert('#' not in new_url)
        if new_url not in self.seen:
            self.queue.put(new_url)
            self.seen.append(new_url)

    def _get_one(self, url):
        """ Download a single URL, and parse it for further URLS """
        # If it's not on this domain, we don't want it
        # This will fuck up fancy websites.

        parsed_url = extract(url)

        if (parsed_url.domain != parsed_root.domain
            or parsed_url.suffix != parsed_root.suffix):
            print(bcolors.OKGREEN,
                  "Ignoring", url,
                  "wrong domain", parsed_url.domain,
                  bcolors.ENDC)
            return

        # Does it exist?
        try:
            req = requests.get(url)
            #print(req.headers)
        except requests.ConnectionError:
            return

        # Does it actually exist?
        # I follow redirects because that's easy
        if req.status_code == requests.status_codes.codes.service_unavailable:
            time.sleep(0.1)
            self.queue.put(url)
            print(bcolors.OKBLUE, "retrying", url, bcolors.ENDC)
            return
        elif req.status_code != requests.codes.ok:
            print(bcolors.FAIL, "fail on", url, "status", req.status_code, bcolors.ENDC)
            return
        else:
            print(url)

        # If it's a text file, parse it for other files we want
        try:
            if 'text' in req.headers['content-type']:
                soup = BeautifulSoup(req.text, "html.parser")
                for link in soup.find_all('a',href=True):
                    self._put_url(url, link['href'])
                for link in soup.find_all('img'):
                    self._put_url(url, link['src'])
        except KeyError:
            pass

        # This is really bad
        rel = url[url.find(parsed_url.suffix)+len(parsed_url.suffix)+1:]
        path = os.path.join(os.getcwd(), rel)

        # Try and create the file structure
        try:
            # if the path has a file extension, don't make the filename a folder
            # otherwise assume it's implicitly index.html
            if is_file.search(path):
                os.makedirs(os.path.dirname(path))
            else:
                os.makedirs(path)
            print(bcolors.UNDERLINE, "  made path", os.path.dirname(path), bcolors.ENDC)
        except FileExistsError:
            print(bcolors.UNDERLINE, "  failed to make path", os.path.dirname(path), bcolors.ENDC)


        # If it's a bare URL, assume it's an index page
        # This might break fancy websites
        if os.path.isdir(path):
            path = os.path.join(path, 'index.html')
            print(bcolors.UNDERLINE, "  added idx", path, bcolors.ENDC)

        with open(path, "wb") as f:
            print(bcolors.UNDERLINE, "  writing to", path, bcolors.ENDC)
            f.write(req.content)


# Seed the system
urls_to_get.put(root)

# Create some shared objects to track our worker drones
manager = mp.Manager()
seenURLs = manager.list([])
workers_working = mp.Value(c_long, 0)
workers_working.value = 0

# Spin up worker drones
getters = [Getter(urls_to_get, workers_working, seenURLs) for _ in range(THREADS)]

# Start our worker drones
for getter in getters:
    getter.start()

# How many worker drones do we start with?
print(bcolors.WARNING,
      "workers:", workers_working.value,
      "queue empty:", urls_to_get.empty(),
      bcolors.ENDC)

# This is weird.
# This is needed to give the drones time to start working so we don't immediately
# run out of stuff to do and stop.
# A sensible design wouldn't need this, but whatever.
time.sleep(2)

# Keep working, worker drones
while workers_working.value != 0 or not urls_to_get.empty():
    print(bcolors.WARNING,
          "workers:", workers_working.value,
          "queue size:", urls_to_get.qsize() if sys.platform != "darwin" else "UNSUPPORTED",
          bcolors.ENDC)
    time.sleep(0.1)

# Kill all the worker drones in a Stalin-esque purge
for _ in getters:
    urls_to_get.put(Stop())
for g in getters:
    g.join()

# Happy days
print('Site downloaded!')



'https://mitpress.mit.edu/sites/default/files/titles/content/sicm/book-Z-H-1.html#titlepage'.split('#')[0]
