# A simple site scraper
Scraper is a terrible Python script to download websites.
It's rather multithreaded, and easier to use than HTTrack.

## Good things
- Fast (probably)
- Real simple to use
- Works on most websites
- *New!* Works on subdomains too!

## Bad things
- You're lucky there's a URL option at all, really. The tool is very barebones.
- If the webserver you're scraping serves binary files without a file
  extension, the script assumes they're an index.html in a folder
  named the same as the file. *This shouldn't really be an issue, but
  if something really weird is going on this could be why.*

## Use
Scraper dumps the site into the current working directory.
If you don't want that, change your current working directory.

> python3 scraper.py url [number_of_threads]

Written in an hour by me and @tomparks

