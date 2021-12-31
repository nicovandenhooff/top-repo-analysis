# Author: Nico Van den Hooff <www.nicovandenhooff.com>
# License: MIT License

"""
Scrapes the following data from a search query on Github:
    - The top n repos (max is 1000) as it relates to the search query, where "top" is calculated
    by total number of stars or forks that a repo has.
    - The data for the owners of the above repos.
    - All of the repository data for the top 25 Github Users for the above repos, where "top" is
    calculated by the number of followers a Github User has.
    - All of the repository data for the top 25 Github Organizations for the above repos, where "top"
    is calculated by the total number of stars an Organization has.

Usage: 
    github_scraper.py [options]
    github_scraper.py (-h | --help)

Options:
    -h --help                         Show this screen.
    -q <queries> --queries=<queries>  The search queries to scrape Gitub for. If multiple queries
                                      are desired, enclose them with "" and seperate each query 
                                      with a comma. [default: Machine Learning,Deep Learning]
    -s <sort> --sort=<sort>           How to sort the repos to scrape, must be "stars" or "forks".
                                      [default: stars]
    -o <order> --order=<order>        How to order the repos to scrape, must be "asc" or "desc".
                                      If "asc" is used then this script scrapes the "bottom" or
                                      least popular repos, as opposed to the "top" or most popular
                                      repos for the search queries on Github.
                                      [default: desc] 
    -n <num> --num=<num>              The number of repos to scrape, max is 1000. [default: 1000]
    -p <path> --path=<path>           The output file path to save the scraped data.
                                      [default: data/scraped/]
"""

import time
import json
import pandas as pd
from tqdm import tqdm
from docopt import docopt
from github import Github, GithubException


def get_top_repos(g, query, sort, order, num):
    """Gets the top n repos for a search query on Github.

    Note: The Github API returns a max of 1000 items per search API request.
          Therefore this method can only return 1000 repos for a given seach
          query.  There are "tricks" to increase this, such as restricting and
          bucketing searches by dates, but they are messy and often result in
          the script taking a long time due to API rate limits.

    Parameters
    ----------
    g : PyGithub Github
        Github object that has been instantiated with an API token.
    query : str
        The query to search Github for.
    sort : str
        How to sort the search results, must be one of ["stars", "forks"].
    order : str
        How to arrange the sort, must be one of ["desc", "asc"].
    num : int
        The number of repos to scrape, maximum possible is 1000.

    Returns
    -------
    top_repos : list of dict
        Github data for the top repos for the given search query.
    """

    if num > 1000:
        print("Error, can only scrape up to 1000 repos")
        return

    top_repos = []

    # gets the top n repos, 1 API call
    repos = g.search_repositories(query, sort=sort, order=order)[:num]

    # extracts repo information for each repo
    for repo in tqdm(repos, desc=f"{query} Repo Scrape", total=num):
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

    for repo in tqdm(repos, desc=f"User Data Scrape"):
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


def scrape_github(token, queries, sort, order, num):
    """Scrapes Github repo and user data for a given search query.

    Able to process multiple search queries.  If this is desired
    pass the queries as a valid python iterable.

    Parameters
    ----------
    token : str
        Github API access token.
    queries : str or list, set, or tuple of str
        The query or queries to search Github for.
    sort : str
        How to sort the search results, must be one of ["stars", "forks"].
    order : str
        How to arrange the sort, must be one of ["desc", "asc"].
    num : int
        The number of repos to scrape, maximum possible is 1000.

    Returns
    -------
    github_data : dict
        Dictionary with k:v pairs as query:(repos, user data)
    """

    if not isinstance(queries, (list, set, tuple)):
        print("Queries must be either a list, set or tuple")
        return

    g = Github(token)
    github_data = dict()

    # multiple search queries
    if isinstance(queries, (list, set, tuple)):
        for query in queries:
            top_repos = get_top_repos(g, query, sort=sort, order=order, num=num)
            user_data = get_user_data(g, top_repos)
            github_data[query] = (top_repos, user_data)
    # single search query
    else:
        top_repos = get_top_repos(g, queries, sort=sort, order=order, num=num)
        user_data = get_user_data(g, top_repos)
        github_data[queries] = (top_repos, user_data)

    return github_data


def scrape_repos(token, usernames):
    """Scrapes all of the repository data for a Github User (individual or organization).

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

    for username in tqdm(usernames, desc=f"Top User/Organization Scrape"):
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
          Script is slept at 3 API request remaining for either
          API in order to be cautious of the limits.

    Parameters
    ----------
    g : PyGithub Github
        Github object that has been instantiated with an API token.
    """

    # current hour and minute
    t = time.localtime()
    h, m = t[3], t[4]

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


def get_top_users_and_orgs(user_data_df, top_repos_df):
    """Gets the top 25 Github Users and top 25 Organizations.

    Note: Top 25 Users are determined based on total followers.
          Top 25 Organizations are determined based on total stars
          for all of an organizations repos.

    Parameters
    ----------
    user_data_df : pandas DataFrame
        DataFrame that contains user data scraped with the scrape_github method.
    top_repos_df : pandas DataFrame
        DataFrame that contains repo data scraped with the scrape_github method.

    Returns
    -------
    tuple of sets
        The top 25 Github Users and top 25 Organizations
    """
    top_users = set(
        user_data_df.sort_values("followers", ascending=False)
        .head(25)
        .query("type == 'User'")["username"]
        .tolist()
    )

    top_organizations = set(
        top_repos_df.query("type == 'Organization'")
        .groupby("username")
        .sum()
        .reset_index()
        .sort_values("stars", ascending=False)["username"]
        .head(25)
        .tolist()
    )

    return top_users, top_organizations


def main(token, queries, sort, order, num, path):
    """Main function that performs the data scrape"""
    top_repos_dfs = []
    user_data_dfs = []

    # gets raw data for top repos and users who own the repos
    github_data = scrape_github(token, queries, sort, order, num)

    # processes raw data into pandas dfs
    for query in queries:
        top_repos = pd.DataFrame(github_data[query][0])
        user_data = pd.DataFrame(github_data[query][1])

        top_repos["subject"] = query
        user_data["subject"] = query

        top_repos_dfs.append(top_repos)
        user_data_dfs.append(user_data)

    top_repos_df = pd.concat(top_repos_dfs).reset_index(drop=True)
    user_data_df = pd.concat(user_data_dfs).reset_index(drop=True)

    top_repos_df.to_csv(f"{path}top-repos.csv", index=False)
    user_data_df.to_csv(f"{path}user-data.csv", index=False)

    # remove id duplicates before top user and org scrape
    top_repos_df = top_repos_df.drop_duplicates(subset="id", keep="first")
    user_data_df = user_data_df.drop_duplicates(subset="id", keep="first")

    # gets raw data for top 25 users and top 25 orgs and processes into pandas dfs
    top_users, top_organizations = get_top_users_and_orgs(user_data_df, top_repos_df)

    top_user_repos_df = pd.DataFrame(scrape_repos(token, top_users))
    top_user_repos_df.to_csv(f"{path}top-user-repos.csv", index=False)

    top_org_repos_df = pd.DataFrame(scrape_repos(token, top_organizations))
    top_org_repos_df.to_csv(f"{path}top-org-repos.csv", index=False)


if __name__ == "__main__":

    print("--Data scraping starting")
    # processes command line arguments as required
    opt = docopt(__doc__)
    opt["--num"] = int(opt["--num"])
    if "," in opt["--queries"]:
        opt["--queries"] = opt["--queries"].split(",")

    # gets github API token
    with open("src/credentials.json") as f:
        credentials = json.load(f)
        api_token = credentials["github_token"]

    # performs data scraping
    main(
        api_token,
        opt["--queries"],
        opt["--sort"],
        opt["--order"],
        opt["--num"],
        opt["--path"],
    )

    print("--Data scraping complete")
