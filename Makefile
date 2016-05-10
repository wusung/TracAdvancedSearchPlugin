BRANCH		= `git rev-parse --abbrev-ref HEAD`
VERSION		= `cat VERSION`

init:
	pip install -r requirements.txt

clean:
	rm -rf build 
	rm -rf TracAdvancedSearch.egg-info/
	rm -rf dist

build:
	python setup.py bdist_egg

rebuild: clean build

patch: 
	bump -p -r
	$(MAKE) tag

major:
	bump -m -r
	$(MAKE) tag

minor:
	bump -n -r
	$(MAKE) tag

tag:
	git add VERSION
	git commit -m "chore: Bump to v$(VERSION)"
	git tag v$(VERSION)
	git push origin $(BRANCH)
