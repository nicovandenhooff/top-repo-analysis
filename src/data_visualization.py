# Author: Nico Van den Hooff <www.nicovandenhooff.com>
# License: MIT License

"""
Visualizes the scraped and preprocessed data from Github

Usage:
    data_cleaning.py [options]
    data_cleaning.py (-h | --help)

Options:
    -h --help                       Show this screen.
    -i <path> --input_path=<path>   The input file path for the clean scraped data. [default: data/cleaned/]
    -o <path> --output_path=<path>  The output file path to save the visualizations. [default: results/]
"""


import os
import numpy as np
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
from docopt import docopt
from vega_datasets import data
from wordcloud import WordCloud
from github_scraper import get_top_users_and_orgs


# allow plotting of large datasets with altair
alt.data_transformers.enable("data_server")


def get_data(input_path):
    top_repos = pd.read_csv(f"{input_path}top-repos.csv", parse_dates=["created"])
    user_data = pd.read_csv(f"{input_path}user-data.csv", parse_dates=["created"])
    location_df = pd.read_csv(
        f"{input_path}user-location-data.csv", parse_dates=["created"]
    )
    top_user_repos = pd.read_csv(
        f"{input_path}top-user-repos.csv", parse_dates=["created"]
    )
    top_org_repos = pd.read_csv(
        f"{input_path}top-org-repos.csv", parse_dates=["created"]
    )

    return top_repos, user_data, location_df, top_user_repos, top_org_repos


def make_wordcloud(df, column, random_state, colormap, output_path, filename):
    words = df[column].dropna()
    words = words[words.map(lambda x: x.isascii())]
    words = " ".join(words.tolist())

    wordcloud = WordCloud(
        width=1000, height=750, random_state=random_state, colormap=colormap
    ).generate(words)

    plt.figure(figsize=(8, 6), dpi=125)
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(f"{output_path}{filename}.png", bbox_inches="tight")


def get_worldclouds(top_repos, user_data, output_path):
    make_wordcloud(
        top_repos, "description", 3, "plasma", output_path, "repo_description_wordcloud"
    )

    make_wordcloud(user_data, "bio", 3, "plasma", output_path, "user_bio_pywordcloud")


def top_10_repos_chart(top_repos):
    top_10_repos = (
        alt.Chart(
            top_repos,
            title=alt.TitleParams(text="Highest star count", anchor="start", dx=201),
        )
        .mark_bar()
        .encode(
            alt.X(
                "stars", scale=alt.Scale(domain=(0, 165000)), title="Number of stars"
            ),
            alt.Y("repo_name", sort="x", title="Repository name"),
            alt.Color("subject", title=None),
            alt.Tooltip(["username", "repo_name", "stars", "language"]),
        )
        .transform_window(
            rank="rank(stars)", sort=[alt.SortField("stars", order="descending")]
        )
        .transform_filter(alt.datum.rank <= 10)
        .properties(height=250, width=375)
    )

    return top_10_repos


def top_10_lang_stars_chart(top_repos):
    language_summary = top_repos.copy()

    # clean up nans and duplicates
    replaced = [np.nan, "MATLAB"]
    values = ["No language", "Matlab"]

    language_summary["language"] = language_summary["language"].replace(
        to_replace=replaced, value=values
    )

    # top 10 languages
    top_languages = (
        language_summary["language"].value_counts()[:10].index.values.tolist()
    )

    # replace any language not in top 10
    language_summary["language"] = language_summary["language"].map(
        lambda x: x if x in top_languages else "Other"
    )

    # tidy summary for visualization
    language_summary = (
        language_summary.groupby(["subject", "language"]).sum().reset_index()
    )

    col_sort = (
        language_summary.query("subject == 'Deep learning'")
        .sort_values("stars", ascending=False)["language"]
        .to_list()
    )

    x_sort = ["Deep learning", "Machine learning"]

    top_10_languages = (
        alt.Chart(
            language_summary,
            title=alt.TitleParams(
                "Most starred programming languages", dy=-5, anchor="middle"
            ),
        )
        .mark_bar()
        .encode(
            alt.X("subject", axis=None, sort=x_sort),
            alt.Y("stars", title="Total stars"),
            alt.Color("subject"),
            alt.Column(
                "language",
                title=None,
                sort=col_sort,
                header=alt.Header(labelFontSize=12),
            ),
            alt.Tooltip("stars"),
        )
        .properties(width=53)
    )

    return top_10_languages


def star_distribution_chart(top_repos):
    stars_df = top_repos[["stars", "subject"]].copy()
    stars_df["log stars"] = np.log(stars_df["stars"])

    star_distribution = (
        alt.Chart(
            stars_df,
            title=alt.TitleParams(
                text="Star count distribution", dx=38, dy=7, anchor="start"
            ),
        )
        .transform_density(
            "log stars", groupby=["subject"], as_=["log stars", "density"]
        )
        .mark_area(opacity=0.6)
        .encode(
            alt.X("log stars", title="Stars (ln)"),
            alt.Y(
                "density:Q",
                title="Density",
            ),
            alt.Color("subject"),
        )
        .properties(height=250, width=375)
    )

    return star_distribution


def get_combined_star_chart(top_repos, output_path):

    top_10_repos = top_10_repos_chart(top_repos)
    top_10_languages = top_10_lang_stars_chart(top_repos)
    star_distribution = star_distribution_chart(top_repos)

    combined_star_chart = (
        alt.vconcat(
            alt.hconcat(top_10_repos, star_distribution),
            top_10_languages,
            title=alt.TitleParams(
                text="Top repositories, stars, and programming languages",
                dy=-8,
                fontWeight="lighter",
                fontSize=25,
            ),
        )
        .configure_axis(labelFontSize=12, titleFontSize=12)
        .configure_title(fontSize=15, anchor="middle", fontWeight="bold")
    )

    combined_star_chart.save(os.path.join(output_path, "combined_star_chart.png"))


def get_datetime_df(top_repos):
    repo_datetime_df = top_repos.set_index("created")
    repo_datetime_df["year"] = repo_datetime_df.index.year
    return repo_datetime_df


def yearly_repo_chart(top_repos):

    repo_datetime_df = get_datetime_df(top_repos)

    yearly_repos = (
        alt.Chart(
            repo_datetime_df,
            title=alt.TitleParams("Repositories created", dy=-5, anchor="middle"),
        )
        .mark_bar()
        .encode(
            alt.X("subject", axis=None),
            alt.Y("count()", title="Total repositories created"),
            alt.Color("subject"),
            alt.Column("year", title=None, header=alt.Header(labelFontSize=12)),
        )
        .properties(width=50, height=300)
    )

    return yearly_repos


def yearly_median_stars_chart(top_repos):

    repo_datetime_df = get_datetime_df(top_repos)

    yearly_median_stars = (
        alt.Chart(
            repo_datetime_df,
            title=alt.TitleParams("Median star count per respository", dy=6),
        )
        .mark_line(point=True)
        .encode(
            alt.X(
                "year",
                title="Year",
                axis=alt.Axis(format="y", labelOverlap=False, labelFlush=False),
                scale=alt.Scale(domain=(2009, 2021)),
            ),
            alt.Y("median(stars)", title="Median star count"),
            alt.Color("subject", legend=None),
            alt.Tooltip("median(stars)"),
        )
        .properties(height=250, width=375)
    )

    return yearly_median_stars


def yearly_topics_chart(top_repos):

    repo_datetime_df = get_datetime_df(top_repos)

    topics_df = repo_datetime_df.explode("topics").dropna(subset=["topics"])

    top_10_topics = (
        topics_df["topics"]
        .value_counts()
        .sort_values(ascending=False)
        .head(10)
        .index.values.tolist()
    )

    top_topics_df = topics_df.query("topics in @top_10_topics")

    yearly_topics = (
        alt.Chart(top_topics_df, title="Popular topics")
        .mark_square()
        .encode(
            alt.X(
                "year",
                axis=alt.Axis(format="y", labelOverlap=False, labelFlush=False),
                scale=alt.Scale(domain=(2009, 2021)),
                title="Year",
            ),
            alt.Y("topics", title="Topic"),
            alt.Color("count()", scale=alt.Scale(scheme="lightorange")),
            alt.Size("count()"),
        )
        .properties(height=250, width=375)
    )

    return yearly_topics


def get_combined_yearly_chart(top_repos, output_path):

    yearly_repos = yearly_repo_chart(top_repos)
    yearly_median_stars = yearly_median_stars_chart(top_repos)
    yearly_topics = yearly_topics_chart(top_repos)

    combined_yearly_chart = (
        alt.vconcat(
            alt.hconcat(yearly_median_stars, yearly_topics).resolve_scale(
                size="independent"
            ),
            yearly_repos,
            title=alt.TitleParams(
                text="How ML and DL evolved from 2009 to 2021",
                dy=-8,
                fontWeight="lighter",
                fontSize=25,
            ),
        )
        .resolve_scale(color="independent")
        .configure_axis(labelFontSize=11, titleFontSize=12)
        .configure_title(fontSize=15, anchor="middle", fontWeight="bold")
    )

    combined_yearly_chart.save(os.path.join(output_path, "combined_yearly_chart.png"))


def user_map_chart(location_df):

    # required for earth outline
    graticule = alt.graticule()
    source = alt.topo_feature(data.world_110m.url, "countries")

    # locations of users
    points = (
        alt.Chart(location_df, title="Location of the top 2000 users")
        .transform_aggregate(
            latitude="mean(latitude)",
            longitude="mean(longitude)",
            count="count()",
            groupby=["country", "continent"],
        )
        .mark_circle()
        .encode(
            longitude="longitude:Q",
            latitude="latitude:Q",
            size=alt.Size(
                "count:Q", scale=alt.Scale(range=(20, 1000)), title="Number of Users"
            ),
            color=alt.Color("continent", title="Continent"),
        )
    )

    # final chart
    location_chart = (
        alt.layer(
            alt.Chart(graticule).mark_geoshape(stroke="white", strokeWidth=0.5),
            alt.Chart(source).mark_geoshape(fill="white", stroke="grey"),
            points,
        )
        .project("naturalEarth1")
        .properties(width=600, height=400)
    )

    return location_chart


def most_followed_users_chart(user_data, top_repos, top_user_repos, location_df):

    top_users, _ = get_top_users_and_orgs(user_data, top_repos)

    top_user_summary_df = (
        top_user_repos.drop("id", axis=1)
        .groupby("username")
        .agg(["sum", "mean", "median"])
    )

    top_user_summary_df.columns = top_user_summary_df.columns.map("-".join)

    top_user_summary_df = top_user_summary_df.reset_index()

    top_user_stats_df = user_data.query("username in @top_users").merge(
        top_user_summary_df, on="username"
    )

    most_followed_users_chart = (
        alt.Chart(
            pd.merge(left=top_user_stats_df, right=location_df),
            title=alt.TitleParams("Most followed users"),
        )
        .mark_bar()
        .encode(
            alt.X("followers", title="Followers"),
            alt.Y("username", sort="x", title="Username"),
            alt.Color("continent"),
            alt.Tooltip("stars-sum"),
        )
        .properties(height=400, width=350)
    )

    return most_followed_users_chart


def get_combined_user_chart(
    location_df, user_data, top_repos, top_user_repos, output_path
):

    user_map = user_map_chart(location_df)
    most_followed_users = most_followed_users_chart(
        user_data, top_repos, top_user_repos, location_df
    )

    combined_user_chart = (
        alt.hconcat(
            most_followed_users,
            user_map,
            title=alt.TitleParams(
                text="The top ML and DL users (individuals)",
                dy=-8,
                fontWeight="lighter",
                fontSize=25,
            ),
        )
        .configure_axis(labelFontSize=12, titleFontSize=12)
        .configure_title(fontSize=15, anchor="middle", fontWeight="bold")
    )

    combined_user_chart.save(os.path.join(output_path, "combined_user_chart.png"))


def org_star_chart(top_org_repos, top_repos, user_data):

    _, top_organizations = get_top_users_and_orgs(user_data, top_repos)

    top_org_summary_df = (
        top_org_repos.drop("id", axis=1)
        .groupby("username")
        .agg(["sum", "mean", "median"])
    )

    top_org_summary_df.columns = top_org_summary_df.columns.map("-".join)

    top_org_summary_df = top_org_summary_df.reset_index()

    top_org_stats_df = user_data.query("username in @top_organizations").merge(
        top_org_summary_df, on="username"
    )

    org_star_chart = (
        alt.Chart(top_org_stats_df, title=alt.TitleParams("Ranked by total stars"))
        .mark_bar()
        .encode(
            alt.X("stars-sum", title="Total stars"),
            alt.Y("username", sort="x", title="Organization"),
        )
    )

    return org_star_chart


def org_lang_charts(top_org_repos):
    org_language_df = top_org_repos[~top_org_repos["language"].isna()]
    org_language_df = org_language_df.query("language != 'Jupyter Notebook'")
    lang_order = ["Python", "C#", "C++", "Java", "JavaScript"]

    org_lang_count_chart = (
        alt.Chart(
            org_language_df,
            title=alt.TitleParams("Top 5 most used programming languages"),
        )
        .transform_aggregate(count="count()", groupby=["language"])
        .transform_window(
            rank="rank(count)", sort=[alt.SortField("count", order="descending")]
        )
        .transform_filter(alt.datum.rank <= 5)
        .mark_bar()
        .encode(
            alt.X("count:Q", title="Repositories that implement it"),
            alt.Y("language", sort="x", title="Language"),
        )
    )

    org_language_df = org_language_df.set_index("created")
    org_language_df["year"] = org_language_df.index.year
    top_5_languages = org_language_df["language"].value_counts().head(5).index.tolist()

    org_lang_year_chart = (
        alt.Chart(
            org_language_df.query("language in @top_5_languages"),
            title=alt.TitleParams("Use of the top 5 languages from 2009-2013"),
        )
        .mark_line(point=True)
        .encode(
            alt.X("year", title="Year", axis=alt.Axis(format="y")),
            alt.Y("count()", title="Repositories using the language"),
            alt.Color("language", sort=lang_order, title=None),
        )
        .properties(height=280)
    )

    return org_lang_count_chart, org_lang_year_chart


def get_combined_org_chart(top_org_repos, top_repos, user_data, output_path):

    org_star = org_star_chart(top_org_repos, top_repos, user_data)
    org_lang_count, org_lang_year = org_lang_charts(top_org_repos)

    combined_org_chart = (
        alt.hconcat(
            org_star,
            alt.vconcat(org_lang_count, org_lang_year).resolve_scale(
                color="independent"
            ),
            title=alt.TitleParams(
                text="Organizations implementing ML and DL and the languages they use",
                dy=-8,
                fontWeight="lighter",
                fontSize=20,
            ),
        )
        .configure_axis(labelFontSize=12, titleFontSize=12)
        .configure_title(fontSize=15, anchor="middle", fontWeight="bold")
    )

    combined_org_chart.save(os.path.join(output_path, "combined_org_chart.png"))


def main(input_path, output_path):

    top_repos, user_data, location_df, top_user_repos, top_org_repos = get_data(
        input_path
    )

    print("--Creating wordclouds")
    get_worldclouds(top_repos, user_data, output_path)

    print("--Creating combined start chart")
    get_combined_star_chart(top_repos, output_path)

    print("--Creating combined yearly chart")
    get_combined_yearly_chart(top_repos, output_path)

    print("--Creating combined user chart")
    get_combined_user_chart(
        location_df, user_data, top_repos, top_user_repos, output_path
    )

    print("--Creating combined organization chart")
    get_combined_org_chart(top_org_repos, top_repos, user_data, output_path)


if __name__ == "__main__":
    print("--Data visualization starting")
    opt = docopt(__doc__)
    main(opt["--input_path"], opt["--output_path"])
    print("--Data visualization complete")
