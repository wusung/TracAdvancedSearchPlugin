# -*- coding: utf-8 -*-
import sys

from setuptools import setup

PACKAGE = 'TracAdvancedSearch'
VERSION = '0.6.1'

REQUIRES = [
	'Trac>=0.11',
	'elasticsearch>=2.0.0',
]

if sys.version_info[:4] < (2, 6):
	REQUIRES.append('simplejson')

CLASSIFIERS = [
	'Framework :: Trac',
	'Development Status :: 4 - Release',
	'Environment :: Web Environment',
	'Intended Audience :: Developers',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Topic :: Software Development',
]

setup(name=PACKAGE,
	version=VERSION,
	description='This plugin allows you to index your wiki and ticket data '
		    'in a full text search engine and search it from a button '
		    'in the main navbar.',
	classifiers=CLASSIFIERS,
	keywords=['trac', 'plugin', 'search', 'full-text-search'],
	author='Wusung Peng',
	author_email='wusungpeng@kkbox.com',
        url="https://github.com/wusung/TracAdvancedSearchPlugin",
	license='SEE LICENSE',
	platforms=['linux', 'osx', 'unix', 'win32'],
	packages=['tracadvsearch'],
	entry_points={'trac.plugins': '%s = tracadvsearch' % PACKAGE},
	package_data={
		'tracadvsearch': [
			'templates/*.html',
			'htdocs/css/*.css',
			'htdocs/js/*.js'
		]
	},
	include_package_data=True,
	install_requires=REQUIRES,
)
