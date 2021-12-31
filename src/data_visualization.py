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

    make_wordcloud(user_data, "bio", 3, "plasma", output_path, "user_bio_wordcloud")


def get_top_10_repos_chart(top_repos, output_path):
    top_10_repos = (
        alt.Chart(
            top_repos,
            # title=alt.TitleParams(text="Most popular repositories", fontSize=20),
        )
        .mark_bar()
        .encode(
            alt.X(
                "stars", scale=alt.Scale(domain=(0, 165000)), title="Number of stars"
            ),
            alt.Y("repo_name", sort="x", title="Repository name"),
            alt.Color("subject", title=None),
        )
        .transform_window(
            rank="rank(stars)", sort=[alt.SortField("stars", order="descending")]
        )
        .transform_filter(alt.datum.rank <= 10)
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14)
    )

    top_10_repos.save(os.path.join(output_path, "top_10_repos.png"))


def get_top_10_lang_stars_chart(top_repos, output_path):
    language_summary = top_repos.copy()

    language_summary = language_summary.dropna(subset=["language"])

    # clean up nans and duplicates
    replaced = ["MATLAB"]
    values = ["Matlab"]

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
        language_summary.query("subject == 'Deep Learning'")
        .sort_values("stars", ascending=False)["language"]
        .to_list()
    )

    x_sort = ["Deep Learning", "Machine Learning"]

    top_10_languages = (
        (
            alt.Chart(
                language_summary,
                # title=alt.TitleParams(
                #     "Most popular programming languages",
                #     dy=-5,
                #     anchor="middle",
                #     fontSize=20,
                # ),
            )
            .mark_bar()
            .encode(
                alt.X("subject", axis=None, sort=x_sort),
                alt.Y("stars", title="Total stars"),
                alt.Color(
                    "subject",
                    title=None,
                    legend=alt.Legend(
                        orient="none",
                        legendX=230,
                        legendY=-50,
                        direction="horizontal",
                        title=None,
                    ),
                ),
                alt.Column(
                    "language",
                    title=None,
                    sort=col_sort,
                    header=alt.Header(labelFontSize=13),
                ),
            )
            .properties(width=53)
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14)
    )

    top_10_languages.save(os.path.join(output_path, "top_10_languages.png"))


def get_star_distribution_chart(top_repos, output_path):
    stars_df = top_repos[["stars", "subject"]].copy()
    stars_df["log stars"] = np.log(stars_df["stars"])

    star_distribution = (
        alt.Chart(
            stars_df,
            # title=alt.TitleParams(text="Distribution of total stars", fontSize=20),
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
            alt.Color("subject", title=None),
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14)
    )

    star_distribution.save(os.path.join(output_path, "star_distribution.png"))


def get_datetime_df(top_repos):
    repo_datetime_df = top_repos.set_index("created")
    repo_datetime_df["year"] = repo_datetime_df.index.year
    return repo_datetime_df


def get_yearly_repo_chart(top_repos, output_path):
    repo_datetime_df = get_datetime_df(top_repos)

    yearly_repos = (
        alt.Chart(
            repo_datetime_df,
            # title=alt.TitleParams(
            #     "When the top repositories were created",
            #     dy=-5,
            #     anchor="middle",
            #     fontSize=20,
            # ),
        )
        .mark_bar()
        .encode(
            alt.X("subject", axis=None),
            alt.Y("count()", title="Total repositories created"),
            alt.Color(
                "subject",
                legend=alt.Legend(
                    orient="none",
                    legendX=250,
                    legendY=-50,
                    direction="horizontal",
                    title=None,
                ),
            ),
            alt.Column("year", title=None, header=alt.Header(labelFontSize=14)),
        )
        .configure_axis(labelFontSize=14, titleFontSize=15)
        .configure_legend(labelFontSize=14)
    )

    yearly_repos.save(os.path.join(output_path, "yearly_repos.png"))


def get_yearly_median_stars_chart(top_repos, output_path):

    repo_datetime_df = get_datetime_df(top_repos)

    yearly_median_stars = (
        alt.Chart(
            repo_datetime_df,
            # title=alt.TitleParams("Median star count per respository", fontSize=20),
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
            alt.Color("subject", title=None),
        )
        .configure_axis(labelFontSize=11, titleFontSize=15)
        .configure_legend(labelFontSize=14)
    )

    yearly_median_stars.save(os.path.join(output_path, "yearly_median_stars.png"))


def get_yearly_topics_chart(top_repos, output_path):

    repo_datetime_df = get_datetime_df(top_repos).dropna(subset=["topics"])
    repo_datetime_df["topics"] = pd.DataFrame(repo_datetime_df["topics"].apply(eval))

    topics_df = repo_datetime_df.explode("topics")

    top_10_topics = (
        topics_df["topics"]
        .value_counts()
        .sort_values(ascending=False)
        .head(10)
        .index.values.tolist()
    )

    top_topics_df = topics_df.query("topics in @top_10_topics")

    yearly_topics = (
        alt.Chart(
            top_topics_df,
            # title=alt.TitleParams("Popular topics over the years", fontSize=20),
        )
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
            alt.Size("count()", title="Total Repositories"),
        )
        .properties(height=275, width=450)
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14, titleFontSize=15)
    )

    yearly_topics.save(os.path.join(output_path, "yearly_topics.png"))


def get_user_location_chart(location_df, output_path):

    # required for earth outline
    graticule = alt.graticule()
    source = alt.topo_feature(data.world_110m.url, "countries")

    # locations of users
    points = (
        alt.Chart(location_df)
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
    user_location_chart = (
        (
            alt.layer(
                alt.Chart(graticule).mark_geoshape(stroke="white", strokeWidth=0.5),
                alt.Chart(source).mark_geoshape(fill="white", stroke="grey"),
                points,
            )
            .project("naturalEarth1")
            .properties(width=600, height=400)
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14, titleFontSize=15)
    )

    user_location_chart.save(os.path.join(output_path, "user_location.png"))


def get_most_followed_users_chart(
    user_data, top_repos, top_user_repos, location_df, output_path
):

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

    domain = ["Asia", "Europe", "North America"]
    range_ = ["#f28e2b", "#e15759", "#76b7b2"]

    most_followed_users_chart = (
        alt.Chart(
            pd.merge(left=top_user_stats_df, right=location_df),
        )
        .mark_bar()
        .encode(
            alt.X("followers", title="Followers"),
            alt.Y("username", sort="x", title="Username"),
            alt.Color(
                "continent",
                scale=alt.Scale(domain=domain, range=range_),
                title="Location",
            ),
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14, titleFontSize=15)
    )

    most_followed_users_chart.save(os.path.join(output_path, "most_followed_users.png"))


def get_org_star_chart(top_org_repos, top_repos, user_data, output_path):

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
        alt.Chart(top_org_stats_df)
        .mark_bar()
        .encode(
            alt.X("stars-sum", title="Total stars"),
            alt.Y("username", sort="x", title="Organization"),
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
    )

    org_star_chart.save(os.path.join(output_path, "org_star_chart.png"))


def get_org_lang_charts(top_org_repos, output_path):
    org_language_df = top_org_repos[~top_org_repos["language"].isna()]
    org_language_df = org_language_df.query("language != 'Jupyter Notebook'")
    lang_order = ["Python", "C#", "C++", "Java", "JavaScript"]

    org_lang_count_chart = (
        alt.Chart(
            org_language_df,
        )
        .transform_aggregate(count="count()", groupby=["language"])
        .transform_window(
            rank="rank(count)", sort=[alt.SortField("count", order="descending")]
        )
        .transform_filter(alt.datum.rank <= 5)
        .mark_bar()
        .encode(
            alt.X("count:Q", title="Repositories that use it"),
            alt.Y("language", sort="x", title="Language"),
            alt.Color("language", sort=lang_order, legend=None),
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
    ).properties(width=460)

    org_language_df = org_language_df.set_index("created")
    org_language_df["year"] = org_language_df.index.year
    top_5_languages = org_language_df["language"].value_counts().head(5).index.tolist()

    org_lang_year_chart = (
        alt.Chart(
            org_language_df.query("language in @top_5_languages"),
        )
        .mark_line(point=True)
        .encode(
            alt.X(
                "year",
                title="Year",
                axis=alt.Axis(format="y", labelOverlap=False, labelFlush=False),
            ),
            alt.Y("count()", title="Repositories that use it"),
            alt.Color("language", sort=lang_order, title=None),
        )
        .configure_axis(labelFontSize=13, titleFontSize=15)
        .configure_legend(labelFontSize=14, titleFontSize=15)
    ).properties(width=500)

    org_lang_count_chart.save(os.path.join(output_path, "org_lang_count.png"))
    org_lang_year_chart.save(os.path.join(output_path, "org_lang_year.png"))


def main(input_path, output_path):

    top_repos, user_data, location_df, top_user_repos, top_org_repos = get_data(
        input_path
    )

    print("--Creating wordclouds")
    get_worldclouds(top_repos, user_data, output_path)

    print("--Creating star charts")
    get_top_10_repos_chart(top_repos, output_path)
    get_top_10_lang_stars_chart(top_repos, output_path)
    get_star_distribution_chart(top_repos, output_path)

    print("--Creating timeseries charts")
    get_yearly_repo_chart(top_repos, output_path)
    get_yearly_median_stars_chart(top_repos, output_path)
    get_yearly_topics_chart(top_repos, output_path)

    print("--Creating user charts")
    get_user_location_chart(location_df, output_path)
    get_most_followed_users_chart(
        user_data, top_repos, top_user_repos, location_df, output_path
    )

    print("--Creating organization charts")
    get_org_star_chart(top_org_repos, top_repos, user_data, output_path)
    get_org_lang_charts(top_org_repos, output_path)


if __name__ == "__main__":
    print("--Data visualization starting")
    opt = docopt(__doc__)
    main(opt["--input_path"], opt["--output_path"])
    print("--Data visualization complete")
