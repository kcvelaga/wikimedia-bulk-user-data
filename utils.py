import pandas as pd
import requests
import json
import time
import urllib.parse


def json_request(url):
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return response.status_code


def key_replace(p_dict, r_dict):
    t_dict = {}
    for k in p_dict.keys():
        t_dict[r_dict[k]] = p_dict[k]
    return t_dict


def get_wikis():
    cdw = pd.read_csv(
        "https://raw.githubusercontent.com/wikimedia-research/canonical-data/master/wiki/wikis.tsv",
        sep="\t",
    )
    cdw["domain_name_srt"] = cdw.domain_name.str.replace(".org", "", regex=True)
    db_domain_map = {}
    for m in cdw[["database_code", "domain_name_srt"]].to_dict("records"):
        db_domain_map[m["database_code"]] = m["domain_name_srt"]

    db_name_map = {}
    for m in cdw[["database_code", "english_name"]].to_dict("records"):
        db_name_map[m["database_code"]] = m["english_name"]

    return cdw, db_domain_map, db_name_map


def user_data_retreiver(username):
    cdw, db_domain_map, db_name_map = get_wikis()
    user_data = {}
    user_data[username] = {}
    username_parsed = urllib.parse.quote(username)

    edits_url = f"https://meta.wikimedia.org/w/api.php?action=query&format=json&list=&meta=globaluserinfo&formatversion=2&guiuser={username_parsed}&guiprop=editcount%7Cgroups%7Cmerged%7Crights"
    json_response = json_request(edits_url)

    user_data[username]["home_wiki"] = db_name_map[
        json_response["query"]["globaluserinfo"]["home"]
    ]
    user_data[username]["global_edits"] = json_response["query"]["globaluserinfo"][
        "editcount"
    ]
    if len(json_response["query"]["globaluserinfo"]["groups"]) == 0:
        user_data[username]["global_groups"] = str(None)
    else:
        user_data[username]["global_groups"] = json_response["query"]["globaluserinfo"][
            "groups"
        ]

    edits_by_wiki, groups_by_wiki, blocks_by_wiki = {}, {}, {}

    if json_response["query"]["globaluserinfo"]["editcount"] > 0:

        merged_wikis = json_response["query"]["globaluserinfo"]["merged"]

        for w in merged_wikis:
            if w["editcount"] > 0:

                if w["wiki"] == "wikidatawiki":
                    edits_by_wiki[w["wiki"]] = w["editcount"] / 5
                else:
                    edits_by_wiki[w["wiki"]] = w["editcount"]

                try:
                    groups_by_wiki[w["wiki"]] = w["groups"]
                except:
                    pass

                try:
                    blocks_by_wiki[w["wiki"]] = [
                        w["blocked"]["expiry"],
                        w["blocked"]["reason"],
                    ]
                except:
                    pass

        top_five_wikis = dict(
            sorted(edits_by_wiki.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        me_wiki = list(top_five_wikis.keys())[0]
        user_data[username]["me_wiki"] = me_wiki
        user_data[username]["me_wiki_group"] = cdw.query(
            """database_code == @me_wiki"""
        ).database_group.values[0]
        user_data[username]["me_wiki_lang"] = cdw.query(
            """database_code == @me_wiki"""
        ).language_name.values[0]

        user_data[username]["edits"] = key_replace(top_five_wikis, db_name_map)
        user_data[username]["groups"] = key_replace(groups_by_wiki, db_name_map)

        if len(blocks_by_wiki) == 0:
            user_data[username]["blocks"] = str(None)
        else:
            user_data[username]["blocks"] = key_replace(blocks_by_wiki, db_name_map)

        articles_by_wiki = {}

        try:
            for w in top_five_wikis.keys():

                domain_srt = db_domain_map[w]
                db_group = cdw.query("""database_code == @w""").database_group.values[0]

                if db_group == "commonswiki":
                    ns_group = [6]
                elif db_group == "wikisource":
                    ns_group = [0, 102, 104, 106, 114]
                else:
                    ns_group = [0]

                n_articles_count = 0
                for ns_id in ns_group:
                    n_articles_url = f"https://xtools.wmflabs.org/api/user/pages_count/{domain_srt}/{username_parsed}/{ns_id}/noredirects/live"
                    json_response = json_request(n_articles_url)
                    try:
                        n_articles_count += json_response["counts"]["count"]
                    except:
                        pass

                articles_by_wiki[w] = n_articles_count

            articles_by_wiki = dict(
                sorted(articles_by_wiki.items(), key=lambda x: x[1], reverse=True)
            )
            user_data[username]["articles"] = key_replace(articles_by_wiki, db_name_map)

        except:
            user_data[username]["articles"] = {"failed to retreive/none"}

    return user_data


def get_user_data(usernames):
    """
    Args:
        usernames (df): dataframe with usernames in a column called 'username'
    Returns:
        user_data (dict): dictionary of user data
    """
    user_names = usernames.username.tolist()
    all_user_data = {}
    failed_users = []
    for u in user_names:
        try:
            all_user_data.update(user_data_retreiver(u))
        except:
            failed_users.append(u)
        
    all_user_data_df = pd.DataFrame(all_user_data).transpose().reset_index().rename({'index': 'user_name'}, axis=1)
    return all_user_data_df, failed_users
