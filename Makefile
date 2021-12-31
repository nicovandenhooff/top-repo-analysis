# Author: Nico Van den Hooff <www.nicovandenhooff.com>
# License: MIT License

all : results/images/

data/scraped/*: src/github_scraper.py
	python src/github_scraper.py --queries="Machine Learning,Deep Learning"

data/cleaned/*: src/data_cleaning.py data/scraped/*
	python src/data_cleaning.py

results/images/: src/data_visualization.py data/cleaned/*
	python src/data_visualization.py


clean:
	rm -f data/cleaned/*
	rm -f data/scraped/*
	rm -f results/images/*
