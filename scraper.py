# -*- coding: utf-8 -*-
from datetime import datetime
import re
import time

import bs4
import scraperwiki


base_url = "https://en.wikipedia.org"
cat_url = "{}/wiki/Category:Elections_in_Gibraltar".format(base_url)
party_dict = {}
sorted_name_re = re.compile(r"^([A-Z]+), (.*)$")

def get_wiki(wiki_link):
    if wiki_link and 'new' not in wiki_link.get('class', []):
        wiki_url = '{}{}'.format(base_url, wiki_link['href'])
        wiki_name = wiki_link['title']
    else:
        wiki_url = None
        wiki_name = None
    return wiki_url, wiki_name

def scrape_table(table_soup):
    data = []
    cols = {
        "party": 0,
        "Name of candidate": 1,
    }
    mapping = {}
    header = table_soup.tr.find_all('td')
    for idx, x in enumerate(header):
        if "party" in x.text.lower():
            mapping["party"] = idx
        if "name" in x.text.lower():
            mapping["name"] = idx
    politicians = table_soup.find_all('tr')[1:]
    for politician in politicians:
        cells = politician.find_all('td')
        if len(cells) == 1:
            break
        p = cells[mapping["name"]]
        name = p.text
        m = sorted_name_re.match(name)
        if m:
            family_name, given_name = m.groups()
            sorted_name = name
            name = "{} {}".format(given_name, family_name)
        else:
            family_name, given_name, sorted_name = None, None, None
        wiki_url, wiki_name = get_wiki(p.a)
        party_short = cells[mapping["party"]].text
        if cells[mapping["party"]].a:
            party = cells[mapping["party"]].a['title']
            party_dict[party_short] = party
        else:
            party = party_dict.get(party_short, party_short)
        data.append({
            "name": name,
            "family_name": family_name,
            "given_name": given_name,
            "sorted_name": sorted_name,
            "group": party,
            "wikipedia": wiki_url,
            "wikipedia_name": wiki_name,
        })
    scraperwiki.sqlite.save(["name"], data, "data")

def scrape_latest(soup):
    party_re = re.compile(r".*? \((.*)\)")
    current_parliament = soup.find(id="Current_membership").find_next('ul').find_all('li')

    data = []
    for x in current_parliament:
        links = x.find_all('a')
        party_initialism = party_re.search(x.text).group(1)
        if len(links) > 1:
            party = links[1]['title']
            party_dict[party_initialism] = party
        else:
            party = party_dict.get(party_initialism, party_initialism)
        name = links[0]['title'].split(' (')[0]
        sort_name = links[0].text
        family_name, given_name = sort_name.split(', ')
        wiki_url, wiki_name = get_wiki(links[0])
        data.append({
            "name": name,
            "group": party,
            "given_name": given_name,
            "family_name": family_name,
            "sort_name": sort_name,
            "wikipedia": wiki_url,
            "wikipedia_name": wiki_name,
        })

    scraperwiki.sqlite.save(["name"], data, "data")

r = scraperwiki.scrape(cat_url)
time.sleep(0.5)
soup = bs4.BeautifulSoup(r, "html.parser")

general_elections = [("{}{}".format(base_url, x['href']), x.text) for x in soup.find_all('a', text=re.compile("general election"))]
for election_url, election_name in general_elections:
    r = scraperwiki.scrape(election_url)
    time.sleep(0.5)
    soup = bs4.BeautifulSoup(r, "html.parser")
    if election_name == "Next Gibraltar general election":
        scrape_latest(soup)
        continue
    cell = soup.find('td', text="Name of candidate")
    if not cell:
        continue
    scrape_table(cell.find_parent('table'))

# hardcode data about this deceased politician
name = "Charles Bruzon"
sort_name = "Bruzon, Charles Arthur"
family_name, given_name = sort_name.split(', ')
death_date = "2013-04-16"
p = {
    "name": name,
    "group": "Gibraltar Socialist Labour Party",
    "death_date": death_date,
    "given_name": given_name,
    "family_name": family_name,
    "sort_name": sort_name,
    "wikipedia": "https://en.wikipedia.org/wiki/Charles_Bruzon",
    "wikipedia_name": name,
}
scraperwiki.sqlite.save(["name"], p, "data")
