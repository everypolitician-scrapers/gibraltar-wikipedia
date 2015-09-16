# -*- coding: utf-8 -*-
from datetime import datetime
import re
import time

import bs4
import scraperwiki


base_url = "https://en.wikipedia.org"
cat_url = "{}/wiki/Category:Elections_in_Gibraltar".format(base_url)
party_dict = {}

def get_wiki(wiki_link):
    if wiki_link and 'new' not in wiki_link.get('class', []):
        wiki_url = '{}{}'.format(base_url, wiki_link['href'])
        wiki_name = wiki_link['title']
    else:
        wiki_url = None
        wiki_name = None
    return wiki_url, wiki_name

def get_names(name):
    name = name.replace('.', '').title()
    name_list = name.split(', ')
    if len(name_list) > 1:
        family_name, given_name = name_list
        initials = ' '.join([x[0] for x in given_name.split()])
        sort_name = name
        name = "{} {}".format(initials, family_name)
    else:
        name_bits = name.split()
        initials = ' '.join([x[0] for x in name_bits[:-1]])
        name = '{} {}'.format(initials, name_bits[-1])
        family_name, given_name, sort_name = None, None, None
    return name, family_name, given_name, sort_name

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
        name = cells[mapping["name"]].text
        if not name:
            break
        name, family_name, given_name, sort_name = get_names(name)
        wiki_url, wiki_name = get_wiki(cells[mapping["name"]].a)
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
            "sort_name": sort_name,
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
        name, family_name, given_name, sort_name = get_names(links[0].text)
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
name = "C A Bruzon"
wikipedia_name = "Charles Bruzon"
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
    "wikipedia_name": wikipedia_name,
}
scraperwiki.sqlite.save(["name"], p, "data")
