# -*- coding: utf-8 -*-
from datetime import datetime
import re

import bs4
import scraperwiki


base_url = "https://en.wikipedia.org"
scrape_url = "{}/wiki/Next_Gibraltar_general_election".format(base_url)

party_re = re.compile(r".*? \((.*)\)")
term = 12

r = scraperwiki.scrape(scrape_url)
soup = bs4.BeautifulSoup(r, "html.parser")

current_parliament = soup.find(id="Current_membership").find_next('ul').find_all('li')

party_dict = {}
data = []
for x in current_parliament:
    start_date = ""
    end_date = ""
    links = x.find_all('a')
    party_initialism = party_re.search(x.text).group(1)
    if party_initialism in party_dict:
        party = party_dict[party_initialism]
    else:
        party = links[1]['title']
        party_dict[party_initialism] = party
    name = links[0]['title'].split(' (')[0]
    sort_name = links[0].text
    if name == "Albert Isola":
        start_date = "2013-07-04"
    wikipedia_url = None
    if 'new' not in links[0].get('class', []):
        wikipedia_url = "{}{}".format(base_url, links[0]['href'])
    data.append({
        "name": name,
        "area": None,
        "group": party,
        "term": term,
        "start_date": start_date,
        "end_date": end_date,
        "sort_name": sort_name,
        "wikipedia": wikipedia_url,
    })

scraperwiki.sqlite.save(["name", "term"], data_list, "data")
