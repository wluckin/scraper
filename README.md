# A simple site scraper
Scraper is a terrible Python script to download websites.
It's rather multithreaded, and easier to use than HTTrack.

## Good things
- Fast (probably)
- Real simple to use
- Works on most websites

## Bad things
- Doesn't work on some websites - assumes all pages that you want are
  served from the same root domain. It will in current state ignore
  subdomains. *Don't be put off if you want this*. It's a 30 second
  change, look at Line 84. 
- You're lucky there's a URL option at all, really

## Use
Scraper dumps the site into the current working directory.
If you don't want that, change your current working directory.

> python3 scraper.py url [number_of_threads]

Written in an hour by me and @tomparks

