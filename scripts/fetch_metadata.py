from SPARQLWrapper import SPARQLWrapper, RDF
from typing import Any
import time

TURTLE_DIR='/home/johannesm/corpus/'

def endpoint_to_data(
        limit: int,
        offset: int,
        sparql: Any = SPARQLWrapper("https://sparql.genenetwork.org/sparql"),
        ) -> Any:
    
    sparql.setReturnFormat(RDF)
    sparql.setQuery(
        f"""
        PREFIX dct: <http://purl.org/dc/terms/> 
        PREFIX gn: <http://genenetwork.org/id/> 
        PREFIX owl: <http://www.w3.org/2002/07/owl#> 
        PREFIX gnc: <http://genenetwork.org/category/> 
        PREFIX gnt: <http://genenetwork.org/term/> 
        PREFIX sdmx-measure: <http://purl.org/linked-data/sdmx/2009/measure#> 
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        PREFIX qb: <http://purl.org/linked-data/cube#> 
        PREFIX xkos: <http://rdf-vocabulary.ddialliance.org/xkos#> 
        PREFIX pubmed: <http://rdf.ncbi.nlm.nih.gov/pubmed/> 

        CONSTRUCT {{
        ?s ?p ?o .
        }}
        WHERE {{
        ?s rdf:type gnc:Phenotype .
        ?s gnt:belongsToGroup gn:setBxd .
        ?s ?p ?o .
        }}
        OFFSET {offset}
        LIMIT {limit}
        """
    )

    return sparql.queryAndConvert()

def data_to_file(
        data: Any,
        chunk_num: int,
        base_path: str = 'rdf_data',
        ) -> Any:
    data.serialize(
        destination=f'{TURTLE_DIR}{base_path}_chunk{chunk_num}.ttl',
        format='turtle')
    print(f'chunk {chunk_num}')

def process(
        limit: int = 1_000, # Explain magic 1_000
        offset: int = 0,
        chunk_num: int = 0,
        time_sleep: int = 5) -> Any: # Explain magic 5
    while True:
        data=endpoint_to_data(
            limit=limit,
            offset=offset)
        if len(data)==0:
            break
        data_to_file(
            data=data,
            chunk_num=chunk_num)
        offset+=limit
        chunk_num+=1
        time.sleep(time_sleep)
try:
    process()
except Exception as e:
    print(e)
    
