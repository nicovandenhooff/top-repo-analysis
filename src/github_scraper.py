# Author: Nico Van den Hooff <www.nicovandenhooff.com>
# License: MIT License

"""
Implements functions used to scrape data from Github.

Usage: 
    github_scraper.py <api_token> [options]
    github_scraper.py (-h | --help)

Options:
    -h --help                         Show this screen.
    -q <queries> --queries=<queries>  The search queries to scrape Gitub for. If multiple queries
                                      are desired, enclose them with "" and seperate each query 
                                      with a comma. [default: Machine Learning, Deep Learning]
    -s <sort> --sort=<sort>           How to sort the repos to scrape, must be "stars", "forks",
                                      or "updated". [default: stars]
    -o <order> --order=<order>        How to order the repos to scrape, must be "asc" or "desc".
                                      [default: desc] 
    -n <num> --num=<num>              The number of repos to scrape, max is 1000. [default: 1000]
    -p <path> --path=<path>           The output file path to save the scraped data. 
                                      [default: data/scraped]
"""

import time
from docopt import docopt
from github import Github, GithubException


def get_top_repos(g, query, sort="stars", order="desc", n=1000):
    """Gets the top repos for a search query on Github.

    Note: The Github API returns a max of 1000 items per search API request.
          Therefore this method returns the top 1000 repos for a given seach
          query.  There are "tricks" around this, such as restricting and
          bucketing searches by dates, but they are messy and often result in
          the script taking a long time due to API rate limits.

    Parameters
    ----------
    g : PyGithub Github
        Github object that has been instantiated with an API token.
    query : str
        The query to search Github for.
    sort : str, by default "stars"
        How to sort the search results, must be one of ["stars", "forks", "updated"].
    order : str, by default "desc"
        How to arrange the sort, must be one of ["desc", "asc"].
    n : int, by default 1000
        The number of repos to scrape, maximum possible is 1000

    Returns
    -------
    top_repos : list of dict
        Github data for the top repos for the given search query.
    """

    if n > 1000:
        print("Error, can only scrape up to 1000 repos")
        return

    top_repos = []

    # gets the top 1000 repos, 1 API call
    repos = g.search_repositories(query, sort=sort, order=order)[:n]

    # extracts repo information for each repo
    for repo in repos:
        check_rate_limit(g)
        top_repos.append(
            {
                "id": repo.id,
                "repo_name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "created": repo.created_at,
                "language": repo.language,
                "type": repo.owner.type,
                "username": repo.owner.login,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "subscribers": repo.subscribers_count,
                "open_issues": repo.open_issues_count,
                "topics": repo.get_topics(),  # uses an additional API call
            }
        )

    return top_repos


def get_user_data(g, repos):
    """Gets detailed user data for the owners of Github repos.

    Parameters
    ----------
    g : PyGithub Github
        Github object that has been instantiated with an API token.
    repos : list of dict
        The repos to scrape individual user data for.  Each dictionary
        must have contain a key "username" that has a corresponding
        Github username as a value.

    Returns
    -------
    user_data : list of dict
        The detailed user data for the owners of the Github repos.
    """
    user_data = []

    for repo in repos:
        check_rate_limit(g)

        # sets the current user, 1 API call
        user = g.get_user(repo["username"])

        # extracts user information
        user_data.append(
            {
                "id": user.id,
                "username": user.login,
                "name": user.name,
                "type": user.type,
                "bio": user.bio,
                "created": user.created_at,
                "company": user.company,
                "email": user.email,
                "location": user.location,
                "hireable": user.hireable,
                "followers": user.followers,
                "following": user.following,
                "public_gists": user.public_gists,
                "public_repos": user.public_repos,
            }
        )

    return user_data


def scrape_github(queries, token, sort="stars", order="desc", n=1000):
    """Scrapes Github repo and user data for a given search query.

    Able to process multiple search queries.  If this is desired
    pass the queries as a valid python iterable.

    Parameters
    ----------
    query : list, set, or tuple of str
        The queries to search Github for.
    token : str
        Github API access token.
    sort : str, by default "stars"
        How to sort the search results, must be one of ["stars", "forks", "updated"].
    order : str, by default "desc"
        How to arrange the sort, must be one of ["desc", "asc"].

    Returns
    -------
    github_data : dict
        Dictionary with k:v pairs as query:(repos, user data)

    Examples
    --------
    >>> query = ["Machine Learning", "Deep Learning"]
    >>> token = "GITHUB_API_TOKEN"
    >>> github_data = scrape_github(query, token)
    """

    if not isinstance(queries, (list, set, tuple)):
        print("Queries must be either a list, set or tuple")
        return

    g = Github(token)
    github_data = dict()

    for query in queries:
        top_repos = get_top_repos(g, query, sort=sort, order=order, n=n)
        user_data = get_user_data(g, top_repos)

        github_data[query] = (top_repos, user_data)

    return github_data


def scrape_repos(token, usernames):
    """Scrapes all of a user or organizations repository data.

    Parameters
    ----------
    token : str
        Github API access token.
    usernames : list, set, or tuple of str
        The usernames to get repo data for.

    Returns
    -------
    all_repos : list of dict
        The repo data for each username.
    """

    if not isinstance(usernames, (list, set, tuple)):
        print("Usernames must be either a list, set or tuple")
        return

    g = Github(token)

    all_repos = []

    for username in usernames:
        check_rate_limit(g)

        try:
            # sets the current user, 1 API call
            user = g.get_user(username)

            for repo in user.get_repos():
                all_repos.append(
                    {
                        "id": repo.id,
                        "repo_name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "created": repo.created_at,
                        "language": repo.language,
                        "type": repo.owner.type,
                        "username": repo.owner.login,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "subscribers": repo.subscribers_count,
                        "open_issues": repo.open_issues_count,
                        "topics": repo.get_topics(),  # uses an additional API call
                    }
                )

        # continue if any exception is thrown besides rate limit
        # which is avoided by check_rate_limit (the API may throw
        # access exceptions due to legal issues etc.)
        except GithubException:
            continue

    return all_repos


def check_rate_limit(g):
    """Checks the Github API rate limits and sleeps script if needed.

    Note: The core API is limited to 5000 requests per hour.
          The search API is limited to 30 requests per minute.

    Parameters
    ----------
    g : PyGithub Github
        Github object that has been instantiated with an API token.
    """

    t = time.localtime()
    h, m = t[3], t[4]

    # sleep at 3 API requests remaining to be safe
    # search API
    if g.get_rate_limit().search.remaining <= 3:
        print("Search API limit met, sleeping for a minute")
        time.sleep(60)
        print("Sleep completed, resuming script")

    # core API
    if g.get_rate_limit().core.remaining <= 3:
        print(f"Core API limit met, sleeping for an hour")
        print(f"Scrape will resume at {h+1}:{m}")
        time.sleep(3600)
        print("Sleep completed, resuming script")


if __name__ == "__main__":
    opt = docopt(__doc__)
    print(opt)
    print(opt["--queries"].split(","))
