
Trac Advanced Search Plugin
============================

An advanced search plugin for the open source Trac project
(http://trac.edgewall.org/). This Trac plugin allows you to use a full-text
search engine (such as Apache Solr) as the search backend for performing
search in Trac.  This plugin also includes a backend for Elasticsearch
(https://www.elastic.co/products/elasticsearch), but other plugins can use the extension point
provided by this plugin to query a different backend.

This plugin is known to be compatible with Trac 0.12 with Elasticsearch 2, as well as
Trac 1.0.11 with Elasticsearch 2.3.2.

See the interface in `plugin-src/advsearch/interface.py` for details about which
methods to implement.

See http://trac.edgewall.org/wiki/TracDev for more information about developing
a Trac plugin.

![Advanced Search Plugin Screenshot][screenshot]

How it works
------------

Once your existing tickets/wiki documents are indexed in the backend you can
make requests using the *Advanced Search* form.  These searches will be handled
by the search backend you have configured in trac.ini.  When new documents or
tickets are added `upsert_document()` will be called on each search backend
to update the index immediately.



Project Status
--------------
Stable, and active.


Requirements
------------

The following python packages are required for the solr backend.

Python client for Elasticsearch (https://pypi.python.org/pypi/elasticsearch)



Installation
------------

This assumes you already have a Trac environment setup.

1. Build and install the plugin
```
cd plugin-src
python setup.py bdist_egg
cp ./dist/TracAdvancedSearch-*.egg <trac_environment_home>/plugins
```

2. Setup the search backend.  If you're using solr, copy and modify the
configuration files provided.
```
cp ./solr/conf/* <solr_home>/conf
```

3. Configure your trac.ini (see the Configuration section below).

4. Restart the trac server. This will differ based on how you are running trac
(apache, tracd, etc).

That's it. You should see an Advanced Search button in the main navbar.



Configuration
-------------

In `trac.ini` you'll need to configure whichever search backend you're using.  If
you're using the default pysolr backend, add something like this:

```
[advanced_search_backend]
elastic_search_url = http://localhost:9200/
timeout = 30

[advanced_search_plugin]
menu_label = Real Search
```

button_label and timeout are both optional.

The default Elasticsearch backend queries to solr for indexing synchronously.
If you want to do indexing asynchronously, add like this:

```
[advanced_search_backend]
async_indexing = true
async_queue_maxsize = 10000  # if 0, the queue size is infinity
...
```

You'll also need to enable the components.

```
[components]
tracadvsearch.advsearch.* = enabled
tracadvsearch.esbackend.* = enabled
```


Remove Search button
--------------------

To disable the old search add the following to `<project_env>/conf/trac.ini`.
Your `trac.ini` may already have a components section.

```
[components]
trac.search.web_ui.SearchModule = disabled
```

[screenshot]: https://raw.github.com/blampe/TracAdvancedSearchPlugin/gh-pages/example.png "Screenshot"
