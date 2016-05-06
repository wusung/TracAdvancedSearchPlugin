#!/usr/bin/env python

from xmlrpclib import ServerProxy
from elasticsearch import Elasticsearch

import argparse
import feedparser
import getpass
import os.path
import pprint
import re
import ssl

USER=''
PASSWORD=''
FROM=0
MAX=100

ELASTIC_SEARCH_URL  = 'http://192.168.24.206:9200'
TRAC_URL            = 'https://%s:%s@issue.kkcorp/trac/rpc'
TRAC_RSS_URL        = 'https://%s:%s@issue.kkcorp/trac/ticket/%s?format=rss'
INDEX = 'trac'
DOC_TYPE = 'ticket'

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

pp = pprint.PrettyPrinter(indent=2)
parser = argparse.ArgumentParser(prog="python " + os.path.basename(__file__))
parser.add_argument("-u", '--username', nargs='?', help="Trac username")
parser.add_argument("-p", '--password', nargs='?', help="Trac password")
parser.add_argument('-e', '--elastic-search-url', nargs='?', help='Elasticsearch API URL')
parser.add_argument('-s', '--start-row', nargs='?', help='Start index of ticket NO')
parser.add_argument('-m', '--max-rows', nargs='?', help='Maximum records of fetching size')
args = parser.parse_args()

if not args.username and not args.password:
   parser.print_help() 
   quit()

USER = args.username

if args.password:
    PASSWORD = args.password
else:
    PASSWORD = getpass.getpass('Trac Password:')

if args.start_row:
    FROM = int(args.start_row)

if args.max_rows:
    MAX = int(args.max_rows)

TRAC_URL            = 'https://%s:%s@issue.kkcorp/trac/rpc' % (USER, PASSWORD)

s = ServerProxy(TRAC_URL, verbose=False, use_datetime=True)
es = Elasticsearch(ELASTIC_SEARCH_URL)

def build_comments(entries):
    comments = ""
    for e in entries:
        comments += ' ' + e.summary_detail.value + ' ' + e.summary
    return re.sub("<.*?>", " ", comments)


def main():

    for i in range(FROM, FROM+MAX):
	try:
            ticket = s.ticket.get(i)
	    info = ticket[3]
	    feed = feedparser.parse(TRAC_RSS_URL % (USER, PASSWORD, i))
	    doc = {
	      "author": info['reporter'],
	      "changetime": ticket[2],
	      "component": info['component'],
	      "ticket_id": ticket[0],
	      "keywords": info['keywords'],
	      "milestone": '',
	      "name": info['summary'],
	      "owner": info['owner'],
	      "priority": info['priority'],
	      "source": 'ticket',
	      "status": info['status'],
	      "description": info['description'],
	      "text": info['description'] + build_comments(feed.entries),
	      "id": 'ticket_' + str(ticket[0]),
	      "ticket_version": '',
	      "time": ticket[1],
	      "type": '',
	    }
	    es.index(INDEX, DOC_TYPE, doc)

	except Exception as e:
	    pp.pprint ('*' * 80)
	    pp.pprint ('ticket id=' + str(i))
            pp.pprint (e)


if __name__ == "__main__":
    main()

