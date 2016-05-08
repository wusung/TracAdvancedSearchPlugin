init:
	pip install -r requirements.txt

build:
	python setup.py bdist_egg

clean:
	rm -rf build dist
