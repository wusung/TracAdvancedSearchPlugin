"""
Backends for TracAdvancedSearchPlugin which implement IAdvSearchBackend.
"""
import datetime
import itertools
import locale
import sys
import threading
import time
import Queue
from operator import methodcaller

from advsearch import SearchBackendException
from interface import IAdvSearchBackend
from interface import IIndexer
from trac.config import ConfigurationError
from trac.core import Component
from trac.core import implements
from trac.search import shorten_result
from elasticsearch import Elasticsearch

# config for elasticsearch
INDEX = 'trac'
DOC_TYPE = 'ticket'
CONFIG_SECTION_NAME = 'advanced_search_backend'
CONFIG_FIELD = {
    'elastic_search_url': (
	    CONFIG_SECTION_NAME,
	    'elastic_search_url',
	    None,
    ),
    'timeout': (
	    CONFIG_SECTION_NAME,
	    'timeout',
	    30,
    ),
    'async_indexing': (
	    CONFIG_SECTION_NAME,
	    'async_indexing',
	    False,
    ),
    'async_queue_maxsize': (
	    CONFIG_SECTION_NAME,
	    'async_queue_maxsize',
	    0,
    ),
    'insensitive_group': (
        CONFIG_SECTION_NAME,
        'insensitive_group',
        'intern,outsourcing',
    ),
    'sensitive_keyword': (
        CONFIG_SECTION_NAME,
        'isensitive_keyword',
        'secret',
    ),        
}


def _get_incremental_value(initial, next_, step):
	""" return incremental value in two stage
	e.g.)
		- step = 0 or 1, return 10
		- step >= 2, return 30
	>>> g = _get_incremental_value(10, 30, 2)
	>>> g.next()
	10
	>>> g.next()
	10
	>>> g.next()
	30
	"""
	for i in itertools.count():
		if i < step:
			yield initial
		else:
			yield next_


class ElasticSearchIndexer(object):
    """Synchronous Indexer for PyElasticSearchBackEnd."""
    implements(IIndexer)

    def __init__(self, backend):
            self.backend = backend

    def upsert(self, doc):
        try:
            self.backend.log.debug(doc)
            self.backend.conn.index(index=INDEX, doc_type=DOC_TYPE, body=doc, id=doc['ticket_id'])
            self.backend.log.debug(doc)
        except Exception, e:
            raise SearchBackendException(e)

    def delete(self, ticket_id):
        try:
            _id = self._query_by_ticket_id(ticket_id)
        except Exception, e:
            raise SearchBackendException(e)

    def _query_by_ticket_id(self, ticket_id):
        doc = {
                "query": {
                  "term": {
                    "ticket_id": ticket_id
                  }
                }
              } 
        res = self.backend.conn.search(
                index=INDEX,
                doc_type=DOC_TYPE,
                body=doc)
        if res["hits"]["total"] != 0:
            for r in res['hits']['hits']:
                _id = r['_id']
                self.backend.conn.delete(index=INDEX, doc_type=DOC_TYPE, id=_id)


class SimpleLifoQueue(list):

	def __init__(self, maxsize=0):
		self.maxsize = maxsize

	def put(self, item):
		if self.maxsize > 0 and len(self) >= self.maxsize:
			raise Queue.Full
		self.append(item)

	def get(self):
		if len(self) > 0:
			return self.pop()
		return None

	def empty(self):
		return len(self) == 0


class AsyncElasticSearchIndexer(threading.Thread):
	"""Asynchronous Indexer for PyElasticSearchBackEnd."""
	implements(IIndexer)

	SLEEP_INTERVAL = (60, 3600, 10)

	def __init__(self, backend, maxsize):
		self.backend = backend
		self.queue = Queue.Queue(maxsize)
		self.recovery_queue = SimpleLifoQueue(maxsize)
		threading.Thread.__init__(self)
		self._name = self.__class__.__name__

	def run(self):
		if self.is_executed_by_trac_admin:
			while self.indexing() and not self.queue.empty():
				pass
			return

		prev_available = False
		interval = self.interval_generator
		while True:
			while self.is_available():
				while self.indexing():
					if not prev_available:
						interval = self.interval_generator  # reset
						prev_available = True
				else:
					prev_available = False
					time.sleep(interval.next())
			else:
				time.sleep(interval.next())

	def indexing(self):
		def get_item():
			if self.recovery_queue.empty():
				return self.queue.get(block=True)
			else:
				return self.recovery_queue.get()

		result = True
		try:
			method_name, item = get_item()
			methodcaller(method_name, item)(self)
		except Exception, e:
			result = False
			self.backend.log.exception(e)
			try:
				self.recovery_queue.put((method_name, item))
			except Queue.Full, e:
				_msg = '%s: Recovery Queue is full, cannot put: %s'
				self.backend.log.error(_msg % (self._name, item))
		else:
			self.queue.task_done()
		return result

	@property
	def is_executed_by_trac_admin(self):
		""" check whether indexing has invoked by trac-admin command

		see below
		https://github.com/dnephin/TracAdvancedSearchPlugin/pull/27
		"""
		rv = False
		if len(sys.argv) >= 1:
			rv = sys.argv[0].find('trac-admin') != -1
		return rv

	@property
	def interval_generator(self):
		return _get_incremental_value(*self.SLEEP_INTERVAL)

	def is_available(self):
		available = False
		try:
			path = '/admin/ping?wt=json'
			res = self.backend.conn._send_request('get', path)
			json = self.backend.conn.decoder.decode(res)
			available = json.get('status') == 'OK'
			if not available:
				self.backend.log.warn('%s: Elasticsearch is not available: %s' % (self._name, r))
		except Exception, e:
			self.backend.log.error('%s: Elasticsearch may be down: %s' % (self._name, e))
		return available

	def upsert(self, doc):
		try:
			self.queue.put(('upsert_index', doc), block=False)
		except Queue.Full, e:
			self.backend.log.error('%s: Queue is full, cannot put: %s' % (self._name, doc))

	def upsert_index(self, doc):
		self.backend.log.debug('%s: upsert id=%s' % (self._name, doc.get('id')))
                self.backend.conn.index(index=INDEX, doc_type=DOC_TYPE, body=doc)

	def delete(self, identifier):
		try:
			self.queue.put(('delete_index', identifier), block=False)
		except Queue.Full, e:
			self.backend.log.error('%s: Queue is full, cannot put: %s' % (self._name, identifier))

	def delete_index(self, identifier):
		self.backend.log.debug('%s: delete id=%s' % (self._name, identifier))
                self.backend.conn.delete(index=INDEX, doc_type=DOC_TYPE, id=identifier)

class PyElasticSearchBackEnd(Component):
        """AdvancedSearchBackend that uses python lib to search Elasticsearch."""
	implements(IAdvSearchBackend)

	SOLR_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
        INPUT_DATE_FORMAT = "%a %b %d %Y %H:%M:%S"
	DEFAULT_DATE_ENCODING = "utf-8"

	SPECIAL_CHARACTERS = r'''+-&|!(){}[]^"~*?:\\'''

	def __init__(self):
		elastic_search_url = self.config.get(*CONFIG_FIELD['elastic_search_url'])
		timeout = self.config.getfloat(*CONFIG_FIELD['timeout'])
		if not elastic_search_url:
			raise ConfigurationError('PyElasticSearchBackend must be configured in trac.ini')
                self.conn = Elasticsearch(elastic_search_url)

		self.async_indexing = self.config.getbool(*CONFIG_FIELD['async_indexing'])
		if self.async_indexing:
			maxsize = self.config.getint(*CONFIG_FIELD['async_queue_maxsize'])
			self.indexer = AsyncElasticSearchIndexer(self, maxsize)
			self.indexer.start()
		else:
			self.indexer = ElasticSearchIndexer(self)

                self.sensitive_keyword = self.config.get(*CONFIG_FIELD['sensitive_keyword']).strip()
                self.insensitive_group = [g.strip().upper() for g in self.config.get(*CONFIG_FIELD['insensitive_group']).split(',')]

	def get_name(self):
		"""Return friendly name for this IAdvSearchBackend provider."""
		return self.__class__.__name__

	def get_sources(self):
		return ('wiki', 'ticket')

	def upsert_document(self, doc):
		doc['time'] = doc['time'].strftime(self.SOLR_DATE_FORMAT)
		self.indexer.upsert(doc)

	def delete_document(self, identifier):
		self.indexer.delete(identifier)

        def query_document(self, ticket_id):
            doc = {
                    "query": {
                      "term": {
                        "ticket_id": ticket_id
                      }
                    }
                  } 
            res = self.conn.search(
                    index=INDEX,
                    doc_type=DOC_TYPE,
                    body=doc)
            if res["hits"]["total"] == "0":
                return None
            return res["hits"]["hits"][0]["_source"]

	def query_backend(self, criteria):
		"""Send a query to elasticsearch."""
                
		# distribute our search query to several fields
                limit = criteria.get('per_page', 15)

                sort = []
		if criteria.get('sort_order') == 'oldest':
                    sort = [{'changetime': { 'order': 'asc' }}]
		elif criteria.get('sort_order') == 'newest':
                    sort = [{'changetime': { 'order': 'desc' }}]
		else: # sort by relevance
		    pass

		# try to find a start offset
                start = 0
		#start_point = criteria['start_points'].get(self.get_name())
		if criteria.get('from'):
		    start = criteria.get('from')
                self.log.debug('start=%s', start)
                size = criteria.get('per_page', 15)

		# add criteria of all fields
		source = self._string_from_filters(criteria.get('source')) or 'wiki ticket'
		author = self._string_from_input(criteria.get('author')) or ''
                username = self._string_from_input(criteria.get('username')) or ''

                q_query = []
                if criteria['q']:
                    q_query = [{
                                "multi_match": {
                                  "query": criteria['q'],
                                  "fuzziness": 2,
                                  "type": "most_fields",
                                  "fields": ["name", "text"],
                                  "operator": "or"
                                }
                              }]

                time_query = []
                if criteria.get('date_start') or criteria.get('date_end'):
                    (sdate, edate) = self._date_from_range(
                            criteria.get('date_start'),
                            criteria.get('date_end'))
                    time_query = [{
                          "range": {
                            "changetime": {
                              "gte": sdate
                            }
                          }
                        }, {
                          "range": {
                            "changetime": {
                              "lte": edate 
                            }
                          }
                        }]

                status = self._string_from_filters(criteria.get('ticket_statuses')) or ''

                status_query = []
                if self._string_from_filters(criteria.get('ticket_statuses')):
                    status_query = [{ "match": { "status": self._string_from_filters(criteria.get('ticket_statuses')) }}]

                source_query = []
                if self._string_from_filters(criteria.get('source')):
                    source_query = [{ "match": { "source": self._string_from_filters(criteria.get('source')) }}]

                author_query = []
                if self._string_from_input(criteria.get('author')):
                    author_query = [{ 'match': { 'author': author }}]

                not_secret_query = []
                if self.sensitive_keyword:
                    not_secret_query = [{
                      "bool": {
                        "must_not": {
                          "term": {"keywords": self.sensitive_keyword}
                        }
                      }
                    }]

                cc_query = []
                if username:
                    cc_query = [{
                                "multi_match": {
                                  "operator": "or",
                                  "query": username,
                                  "fuzziness": 2,
                                  "fields": [
                                    "cc",
                                    "owner",
                                    "author"
                                  ],
                                  "type": "most_fields"
                                }
                              }]

                perms = criteria.get('perms')

                is_trac_admin = 'TRAC_ADMIN' in perms

                self.log.debug([k.upper() for k, v in perms.iteritems()])
                self.log.debug(self.insensitive_group)
                is_insensitive = len([i for i in [k.upper() for k, v in perms.iteritems()] \
                        if i.upper() in self.insensitive_group]) > 0
                self.log.debug("is_trac_admin=%s, is_insensitive=%s", is_trac_admin, is_insensitive)
                if is_trac_admin:
                #if False:
                    # query doc for admin users
                    doc_type = 'admin'
                    doc = {
                        "query": {
                          "bool": {
                            "must": [] 
                              + q_query
                              + status_query 
                              + source_query 
                              + author_query
                              + time_query
                          }
                        },
                        "from": start,
                        "size": size,
                        "sort": sort
                    } 
                elif is_insensitive:
                #elif False:
                    # query doc for restricted users (e.q. intern or outsourcing)
                    doc_type = 'insensitive'
                    doc = {
                      "query": {
                          "bool": {
                            "must": [] 
                              + q_query
                              + cc_query
                              + status_query 
                              + source_query 
                              + author_query
                              + time_query
                          }
                        },
                        "from": start,
                        "size": size,
                        "sort": sort
                      } 
                else: 
                    # query doc for non-admin users
                    doc_type = 'auth_user'

                    # all tickets belongs to the user
                    auth_doc = [{
                        "bool": {
                            "must": []
                                    + q_query
                                    + cc_query
                                    + status_query
                                    + source_query
                                    + author_query
                                    + time_query
                        }
                    }]

                    # all non-secret tickets
                    not_secret_doc = [{
                        "bool": {
                            "must": []
                                    + q_query
                                    + status_query
                                    + source_query
                                    + author_query
                                    + time_query
                                    + not_secret_query
                        }
                    }]

                    doc = {
                        "query": {
                            "constant_score": {
                                "filter": {
                                    "bool": {
                                        "should": [] + auth_doc + not_secret_doc
                                    }
                                }
                            }
                        }
                    }

                self.log.debug('The query doc is %s=%s' % (doc_type, doc))
                
                results = self.conn.search(
                        index=INDEX,
                        doc_type=DOC_TYPE,
                        body=doc)
	        # restruct the results	
                def _to_result(v):
                    i = v["_source"]
                    i["score"] = v["_score"]
                    return i
                return (results["hits"]["total"], 
                    [_to_result(v) for v in results["hits"]["hits"]])

	def _build_summary(self, text, query):
		"""Build a summary which highlights the search terms."""
		if not query:
			return text[:500]
		if not text:
			return ''

		return shorten_result(text, query.split(), maxlen=500)

	def _date_from_solr(self, date_string):
		"""Return a human friendly date from solr date string."""
		def safe_decode(date_string):
			if isinstance(date_string, str):
				lang, encoding = locale.getlocale()
				encoding = encoding if encoding else self.DEFAULT_DATE_ENCODING
				return unicode(date_string, encoding)
			return date_string

		date = self._strptime(date_string, self.SOLR_DATE_FORMAT)
		return safe_decode(date.strftime(self.INPUT_DATE_FORMAT))

	def _string_from_input(self, value):
		"""Return a value string formatted in solr query syntax."""
		if not value:
			return None

		if type(value) in (list, tuple):
			return (" ".join(['"%s"' % v for v in value if v]))

		return value

	def _string_from_filters(self, filter_list):
		if not filter_list:
			return None

		name_list = [f['name'] for f in filter_list if f['active']]
		if not name_list:
			return None

		# add filters that are set as active
		return (' '.join(name_list))

	def _date_from_range(self, start, end):
		"""Return a date range in solr query syntax."""
		if not start and not end:
                    return (None, None)
		if start:
                    start_formatted = self._format_date(start + ' 0:0:0')
		else:
                    start_formatted = self._format_date('Fri Jan 1 1970 0:0:0')
		if end:
                    end_formatted = self._format_date(end + ' 23:59:59')
		else:
                    end_formatted = self._format_date('Fri Jan 1 2200 23:59:59')
		return (start_formatted, end_formatted)

	def _format_date(self, date_string, default="*"):
		"""Format a date as a solr date string."""
		try:
			date = self._strptime(
				date_string, self.INPUT_DATE_FORMAT)
		except ValueError:
			self.log.warn("Invalid date format: %s" % date_string)
			return default
                return date

	def _strptime(self, date_string, date_format):
		return datetime.datetime(*(time.strptime(date_string, date_format)[0:6]))

        def _strp_stime(self, date_string, date_fomrat):
		return datetime.datetime(*(time.strptime(date_string, date_format)[0:6]))

	def _strp_etime(self, date_string, date_format):
		return datetime.datetime(*(time.strptime(date_string, date_format)[0:6]))

        def _print_hits(results):
                " Simple utility function to print results of a search query. "
                print_search_stats(results)
                for hit in results['hits']['hits']:
                    # get created date for a repo and fallback to authored_date for a commit
                    created_at = parse_date(hit['_source'].get('created_at', hit['_source']['authored_date']))
                    print('/%s/%s/%s (%s): %s' % (
                    hit['_index'], hit['_type'], hit['_id'],
                    created_at.strftime('%Y-%m-%d'),
                    hit['_source']['description'].replace('\n', ' ')))

                print('=' * 80)
                print()

