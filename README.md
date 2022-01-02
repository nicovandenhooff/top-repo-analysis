# Exploring the Top ML and DL GitHub Repositories

This repository contains my work related to my project where I collected data on the most popular machine learning and deep learning GitHub repositories in order to further visualize and analyze it.

<!--Note: Add medium link-->
I've written a corresponding Medium article about this project, which you can find HERE (to add link).

At a high level, my analysis is as follows:

1. I collected data on the top machine learning and deep learning repositories and their respective owners from GitHub.
2. I cleaned and prepared the data.
3. I visualized what I thought were interesting patterns, trends, and findings within the data, and discuss each visualization in detail.

Please read the Medium article if you are interested in learning about my analysis in detail!

### Tools used

<p>
<a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/language-python-3776AB?logo=Python&logoColor=white"></a>
<a href="https://numpy.org/"><img alt="NumPy" src="https://img.shields.io/badge/library-NumPy-013243?logo=numpy&logoColor=white"></a>
<a href="https://pandas.pydata.org/"><img alt="pandas" src="https://img.shields.io/badge/library-pandas-150458?logo=pandas&logoColor=white"></a>
<a href="https://github.com/tqdm/tqdm"><img alt="tqdm" src="https://img.shields.io/badge/library-tqdm-FFC107?logo=tqdm&logoColor=white"></a>
<a href="https://pygithub.readthedocs.io/en/latest/"><img alt="PyGitHub" src="https://img.shields.io/badge/library-PyGitHub-861AF7?"></a>
<a href="https://geopy.readthedocs.io/en/stable/"><img alt="GeoPy" src="https://img.shields.io/badge/library-geopy-861AF7?"></a>
<a href="https://altair-viz.github.io/"><img alt="Altair" src="https://img.shields.io/badge/library-Altair-861AF7?"></a>
<a href="https://github.com/tqdm/tqdm"><img alt="tqdm" src="https://custom-icon-badges.herokuapp.com/badge/library-matplotlib-861AF7?logo=matplotlib"></a>
<a href="http://amueller.github.io/word_cloud/"><img alt="wordcloud" src="https://img.shields.io/badge/library-wordcloud-861AF7?"></a>
<a href="http://docopt.org/"><img alt="docopt" src="https://img.shields.io/badge/library-docopt-861AF7?"></a>
<a href="https://black.readthedocs.io/en/stable/index.html"><img alt="black" src="https://img.shields.io/badge/code%20style-black-black?"></a>
    </p>

## Replicating the Analysis

I've designed the analysis in this repository so that anyone is able to recreate the data collection, cleaning, and visualization steps in a fully automated manner.  To do this, open up a terminal and follow the steps below:

**Step 1: Clone this repository to your computer**
```bash
# clone the repo
git clone https://github.com/nicovandenhooff/top-repo-analysis.git

# change working directory to the repos root directory
cd top-repo-analysis
```
**Step 2:  Create and activate the required virtual environment**
```bash
# create the environment
conda env create -f environment.yaml

# activate the environment
conda activate top-repo-analysis
```

**Step 3: Obtain a GitHub personal access token ("PAT") and add it to the credentials file**
Please see how to obtain a PAT [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).  

Once you have it perform the following:
```bash
# open the credentials file
open src/credentials.json
```
This will open the credentials `json` file which contains the following:
```json
{
"github_token": "<TOKEN>"
}
```
Change `<TOKEN>` to your PAT.

**Step 4: Run the following command to delete the current data and visualizations in the repository**
```bash
make clean
```
**Step 5: Run the following command to recreate the analysis**
```bash
make all
```

Please note that if you are recreating the analysis:
- The last step will take several hours to run (approximately 6-8 hours) as the data collection process from GitHub has to sleep to respect the GitHub API rate limit.  The total number of API requests for the data collection will approximately be between 20,000 to 30,000.
- When the data cleaning script `data_cleaning.py` runs, there make be some errors may be printed to the screen by `GeoPy` if the `Noinatim` geolocation service is unable to find a valid location for a GitHub user.  This will not cause the script to terminate, and is just ugly in the terminal.  Unfortunately you cannot suppress these error messages, so just ignore them if they occur.
- Getting the location data with `GeoPy` in the data cleaning script also takes about 30 minutes as the `Nominatim` geolocation service limits 1 API request per second.
- I ran this analysis on December 30, 2021 and as such collected the data from GitHub on this date.  If you run this analysis in the future, the data you collect will inherently be slightly different if the machine learning and deep learning repositories with the highest number of stars has changed since the date when I ran the analysis.  This will slightly change how the resulting visualizations look.

## Using the Scraper to Collect New Data

You can also use the scraping script in isolation to collect new data from GitHub if you desire.

If you'd like to do this, all you'll need to do is open up a terminal, follow steps 1 to 3 above, and then perform the following:

**Step a) Run the scraping script with your desired options as follows**
```bash
python src/github_scraper.py --queries=<queries> --path=<path>
```
- Replace `<queries>` with your desired queries.  Note that if you desire multiple search queries, enclose them in `""` separate them by a single comma with NO SPACE after the comma.  For example `"Machine Learning,Deep Learning"`
- Replace `<path>` with the output path that you want the scraped data to be saved at.

Please see the documentation in the header of the [scraping script](https://github.com/nicovandenhooff/top-repo-analysis/blob/main/src/github_scraper.py) for additional options that are available.

**Step b) Run the data cleaning script to clean your newly scraped data**
```
python src/data_cleaning.py --input_path=<path> --output_path=<output_path>
```
- Replace `<input_path>` with the path that you saved the scraped data at.
- Replace `<output_path>` with the output path that you want the cleaned data to be saved at.
- As metioned in the last section, some errors may be printed to the terminal by `GeoPy` during the data cleaning process, but feel free to ignore these as they do not affect the execution of the script.

## Dependencies

Please see the [environment file](https://github.com/nicovandenhooff/top-repo-analysis/blob/main/environment.yaml) for a full list of dependencies.

## License

The source code for the site is licensed under the [MIT license](https://github.com/nicovandenhooff/top-repo-analysis/blob/main/LICENSE).