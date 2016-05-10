
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

The following python packages are required for the Elasticsearch backend.

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

2. Configure your trac.ini (see the Configuration section below).

3. Restart the trac server. This will differ based on how you are running trac
(apache, tracd, etc).

That's it. You should see an Advanced Search button in the main navbar.



Configuration
-------------

In `trac.ini` you'll need to configure whichever search backend you're using.  If
you're using the default elasticsearch  backend, add something like this:

```
[advanced_search_backend]
elastic_search_url = http://localhost:9200/
timeout = 30

[advanced_search_plugin]
menu_label = Advanced Search
```

button_label and timeout are both optional.

For *insensitive_group*, which means users in these groups will be granted to query the tickets only if he/she is reporter, ticket owner, or in cc list.

For *sensitive_keyword* sets to secret, which means the tickets with keyword *secret* only can be viewed or searched by the owner, reporter, TRAC_ADMIN or in cc list. 
```
[advanced_search_backend]

insensitive_group = intern,outsourcing
sensitive_keyword = secret
```

*insensitive_group* and *sensitive_keyword* are both optional. The fault value of insensitive_group is 'intern,outsourcing'. The default value of sensitive_keyword is 'secret'.


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
