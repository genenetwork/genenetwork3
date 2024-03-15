""""module contains code to fetch the data only from pubmed
At the moment we are only searching in pubmed db but this
feature can be extended to others e.g pmc
"""


import functools
import json
from Bio import Entrez


def fetch_pub_details(id_list, db_name, retmode="xml", email="alexanderkabua@gmail.com"):
    """fetch details of publocation based on their ids
    Args:
        id_list(list): List of publications iDs (pubmed)
        email: (str,optional)

    Returns:
          list:   details of fetched publications

    """
    Entrez.email = email
    if db_name.lower() == "pubmed":
        handle = Entrez.efetch(db=db_name, retmode="xml",
                               id=",".join(id_list))
        results = Entrez.read(handle)
        handle.close()

        return extract_pub_metadata(results)


def extract_pub_metadata(papers):
    """
    Extract metadata from PubMed papers.

    Args:
        papers (dict): Dictionary containing PubMed papers.

    Returns:
        list: Extracted metadata for the papers.
    """
    metadata = {}
    for paper in papers["PubmedArticle"]:

        article = paper['MedlineCitation']['Article']
        author_list = article.get('AuthorList')

        authors = ",".join([f'{author.get("ForeName","")} {author.get("LastName", "")}'
                             for author in author_list])
        abstract = article.get(
            'Abstract', {}).get('AbstractText', '')
        if isinstance(abstract, list):
            abstract = ' '.join(abstract)
        pub_id = str(paper["MedlineCitation"]["PMID"])
        metadata[pub_id] = {
            "pub_id": str(paper["MedlineCitation"]["PMID"]),
            "title": article.get('ArticleTitle'),
            "authors": authors,
            "abstract": abstract,
            "journal_title": article['Journal']['Title'],
            "languages": article.get("Language", ""),
            "source": f"https://pubmed.ncbi.nlm.nih.gov/{pub_id}/"
        }

    return metadata


def fetch_pubmed_id(query, db_name, max_search_count, ret_mode="xml", email="alexanderkabua@gmail.com"):
    """method to fetch the id for a given search in pubmed"""

    Entrez.email = email
    handle = Entrez.esearch(db=db_name, sort="relevance",
                            retmax=max_search_count, ret_mode="xml", term=query)
    results = Entrez.read(handle)
    handle.close()
    if results.get("IdList"):
        return {
            "query": query,
            "id_list": results.get("IdList")
        }


def fetch_all_queries(input_file, max_search_count=1, db_name="pubmed"):
    """
    Search pubmed for publication from json files with values being query string
    Args:
        input_file: (str): path to the json file with the query strings
        max_search_count: no of ids/lookups per each search
        db_name:  target db default pubmed


    returns: (Result<(pub_medata:list,doc_ids:dict),Error)

    """
    try:

        pub_data = []
        doc_ids = {}
        with open(input_file, "r") as file_handler:
            search_dict = json.load(file_handler)

            for (filename, file_obj) in search_dict.items():
                query_ids = fetch_pubmed_id(query=file_obj.get("doc_name"),
                                            db_name=db_name, max_search_count=max_search_count)
                if query_ids:
                    for doc_id in query_ids.get("id_list"):
                        doc_ids[doc_id] = filename
                    pub_data.append(query_ids)

        return (fetch_pub_details(functools.reduce(
            lambda lst1, lst2: lst1 + lst2, [data.get("id_list") for data in pub_data]), db_name), doc_ids)

    except Exception as error:
        raise error


def dump_all_to_file(response, doc_ids, output_file):
    """
    function to map the pubmed data to doc_ids and dump to a json file
    """

    data = {}

    for (pub_id, pub_meta) in response.items():
        doc_id = doc_ids.get(pub_id)
        if data.get(doc_id):
            data[doc_id].append(pub_meta)
        else:
            data[doc_id] = [pub_meta]

    #
    with open(output_file, "w+") as file_handler:
        json.dump(data, file_handler, indent=4)


# lossy method to fetch pub  data
def fetch_id_lossy_search(query, db_name, max_results):
    """
    Search PubMed data based on the provided search string.

    Args:
    - search_string (str): The search string.

    Returns:
    - dict: Dictionary containing search results and status code.
    """

    try:
        response = requests.get(f"http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={db_name}&retmode=json&retmax={max_results}&term={query}",
                                headers={"content-type": "application/json"}
                                )
        return response["esearchresult"]["idlist"]

    except requests.exceptions.RequestException as error:
        raise error


def search_pubmed_lossy(pubmed_id, db_name):
    """
    Fetches records based on the PubMed ID.

    Args:
    - pubmed_id (str): PubMed ID.

    Returns:
    - dict: Records fetched based on PubMed ID.
    """
    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db_name}&id={",".join(pubmed_id)}&retmode=json'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if db_name.lower() == "pmc":
        return data['pmc-articleset']['article']
    return data["PubmedArticleSet"]["PubmedArticle"]


if __name__ == '__main__':
    (pub_data, doc_ids) = fetch_all_queries(
        input_file="parsed_all_files.json", max_search_count=1)
    dump_all_to_file(pub_data, doc_ids, "output_file.json")
