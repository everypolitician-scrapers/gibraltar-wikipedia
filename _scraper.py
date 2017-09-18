# -*- coding: utf-8 -*-
from datetime import datetime
import os
import re
import time

import bs4
import requests
import scraperwiki


base_url = "https://en.wikipedia.org"
cat_url = "{}/wiki/Category:Elections_in_Gibraltar".format(base_url)
party_dict = {}

def get_terms_dict():
    r = requests.get("https://api.morph.io/andylolz/gibraltar-parliament/data.json", params={
      'key': os.environ.get('MORPH_API_KEY'),
      'query': "select `id`, `start_date` from `terms`",
    }, verify=False).json()
    time.sleep(0.5)
    return {x['start_date'][:4]: x['id'] for x in r}

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

def scrape_table(table_soup, term):
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

        party_texts = cells[mapping["party"]].text.split('/')
        parties = []
        for idx, party_text in enumerate(party_texts):
            party = party_dict.get(party_text, party_text)
            if party == party_text:
                party_links = cells[mapping["party"]].find_all('a')
                if party_links:
                    party_link_text = party_links[idx].text
                    party = party_dict.get(party_link_text, party_link_text)
                    if party == party_link_text:
                        party = party_links[idx]['title']
                        party_dict[party_link_text] = party
            parties.append(party)
        data.append({
            "name": name,
            "family_name": family_name,
            "given_name": given_name,
            "sort_name": sort_name,
            "group": ' / '.join(parties),
            "term": term,
            "wikipedia": wiki_url,
            "wikipedia_name": wiki_name,
        })
    scraperwiki.sqlite.save(["name", "term"], data, "data")

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
            "term": max(terms_dict.values()),  # this is v hacky!
            "given_name": given_name,
            "family_name": family_name,
            "sort_name": sort_name,
            "wikipedia": wiki_url,
            "wikipedia_name": wiki_name,
        })

    scraperwiki.sqlite.save(["name", "term"], data, "data")

terms_dict = get_terms_dict()

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
    term = terms_dict[election_name[-4:]]
    scrape_table(cell.find_parent('table'), term)

# hardcode data about this deceased politician
sort_name = "Bruzon, Charles Arthur"
family_name, given_name = sort_name.split(', ')
p = {
    "name": "C A Bruzon",
    "group": "Gibraltar Socialist Labour Party",
    "term": max(terms_dict.values()),  # this is v hacky!
    "death_date": "2013-04-16",
    "given_name": given_name,
    "family_name": family_name,
    "sort_name": sort_name,
    "wikipedia": "https://en.wikipedia.org/wiki/Charles_Bruzon",
    "wikipedia_name": "Charles Bruzon",
}
scraperwiki.sqlite.save(["name", "term"], p, "data")
