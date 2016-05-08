init:
	pip install -r requirements.txt

clean:
	rm -rf build 
	rm -rf TracAdvancedSearch.egg-info/
	rm -rf dist

build:
	python setup.py bdist_egg

rebuild: clean build
