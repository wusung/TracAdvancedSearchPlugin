init:
	pip install -r requirements.txt

clean:
	rm -rf build dist

build:
	python setup.py bdist_egg

rebuild: clean build
