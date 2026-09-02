"""
This scripts runs through a demo on the use of RAG system for genomic analysis
Reasoning based on tree-of-thought
Embedding model = Qwen/Qwen3-Embedding-0.6B
Generative model = calme-3.2-instruct-78b-Q4_K_S
Summary model = Phi-3-mini-4k-instruct-fp16
python rag_script.py
"""
import click
import os
import sys

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.retrievers.ensemble import EnsembleRetriever
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate

from rdflib import Graph
from glob import glob

from tqdm import tqdm

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# XXX: Remove hard-coded paths
CORPUS_PATH="/home/johannesm/corpus/"

# XXX: Remove hard-coded paths.
GENERATIVE_MODEL=LlamaCpp(
    model_path="/home/johannesm/pretrained_models/calme-3.2-instruct-78b-Q4_K_S.gguf",
    max_tokens=1_000,
    n_ctx=32_768,
    seed=2_025,
    temperature=0,
    verbose=False)

# XXX: Remove hard-coded paths.
SUMMARY_MODEL=LlamaCpp(
    model_path="/home/johannesm/pretrained_models/Phi-3-mini-4k-instruct-fp16.gguf",
    max_tokens=500,
    n_ctx=4096,
    seed=2025,
    temperature=0,
    verbose=False)


# Our templates for our simple RAG system
RAG_TEMPLATE="""
Relevant information:
{context}
History:
{chat_history}
Provide a concise answer to the question below. Check first in the history above. If you do not find the answer to the question, use the relevant information above. Do not add any external information.
Explore different reasoning by emulating a conversation between 3 experts. All experts will write down 1 step of their thinking, then share with the group. Then all experts will go on to the next step and so on. If any expert realizes his wrong at any point, he should leave the conversation. Give me only the final answer.
The question is:
{input}
"""

RETRIEVER_TEMPLATE="""
Given the following conversation, generate a search query to retrieve relevant documents.
Conversation:
{input}
"""

SUMMARY_TEMPLATE="""
Summarize the conversations and update with the new lines. Be as concise as possible without loosing key information.
Current summary:
{summary}
New lines of conversation:
{new_lines}
New summary:
"""

@dataclass
class GNQNA_RAG():
    corpus_path: str
    rag_template: str
    retriever_template: str
    summary_template: str
    docs: list = field(init=False)
    memory: Any = field(init=False)
    retrieval_chain: Any = field(init=False)
    ensemble_retriever: Any = field(init=False)
    rag_prompt: Any = field(init=False)
    retriever_prompt: Any = field(init=False)
    summary_prompt: Any = field(init=False)
    chroma_db: Any = field(init=False)

    def __post_init__(self):
        self.docs=self.corpus_to_docs(self.corpus_path)
        self.chroma_db=self.set_chroma_db(
            docs=self.docs,
            embed_model=HuggingFaceEmbeddings(
                model_name="Qwen/Qwen3-Embedding-0.6B"),
            db_path='/home/johannesm/tmp/chroma_db'
        )

        # Init'ing the ensemble retriever
        bm25_retriever=BM25Retriever.from_texts(self.docs)
        bm25_retriever.k=20   # KLUDGE: Explain why the magic number 20
        self.ensemble_retriever=EnsembleRetriever(
            retrievers=[self.chroma_db.as_retriever(), bm25_retriever],
            weights=[0.3, 0.7])  # KLUDGE: Explain why the magic array

        # Init'ing the prompts
        self.rag_prompt=PromptTemplate(
            input_variables=['context', 'question', 'summary'],
            template=self.rag_template)
        self.retriever_prompt = PromptTemplate(
            input_variables=['input'],
            template=self.retriever_template)
        self.summary_prompt = PromptTemplate(
            input_variables=['input'],
            template=self.summary_template)

        # Building the modes.
        # KLUDGE: Consider pickling as a cache mechanism
        self.memory=ConversationSummaryBufferMemory(
            llm=SUMMARY_MODEL,
            memory_key='chat_history',
            input_key='input',
            output_key='answer',
            prompt=self.summary_prompt,
            max_token_limit=1_000,
            return_messages=True)
        self.retrieval_chain = create_retrieval_chain(
            combine_docs_chain=create_stuff_documents_chain(
                llm=GENERATIVE_MODEL,
                prompt=self.rag_prompt),
            retriever=create_history_aware_retriever(
                retriever=self.ensemble_retriever,
                llm=GENERATIVE_MODEL,
                prompt=self.retriever_prompt))

    def corpus_to_docs(self, corpus_path: str) -> list:
        """Convert a corpus into an array of sentences.
        KLUDGE: XXXX: Corpus of text should be RDF.  This here
        is for testing.
        """
        if not Path(corpus_path).exists():
            sys.exit(1)

        turtles=glob(f"{corpus_path}rdf_data*.ttl")
        g=Graph()
        for turtle in turtles:    
            g.parse(turtle, format='turtle')
        docs=[]
        for subject in set(g.subjects()):
            text=f"Entity: {subject}\n"
            for predicate, obj in g.predicate_objects(subject):
                text+=f"{predicate}: {obj}\n"
            docs.append(text)
            return docs[:100_000]


        
    def set_chroma_db(self, docs: list,
                      embed_model: Any, db_path: str,
                      chunk_size: int = 500) -> Any:
        match Path(db_path).exists():
            case True:
                db=Chroma(
                    persist_directory=db_path,
                    embedding_function=embed_model
                )
                return db
            case _:
                for i in tqdm(range(0, len(docs), chunk_size)):
                    chunk=docs[i:i+chunk_size]
                    db=Chroma.from_texts(
                        texts=chunk,
                        embedding=embed_model,
                        persist_directory=db_path)
                    db.persist()
                return db

    def ask_question(self, question: str):
        memory_var=self.memory.load_memory_variables({})
        chat_history=memory_var.get('chat_history', '')
        result=self.retrieval_chain.invoke(
            {'input': question,
             'chat_history': chat_history})
        answer=result.get("answer")
        citations=result.get("context")
        self.memory.save_context(
            {'input': question},
            {'answer': answer})
        # Close LLMs
        GENERATIVE_MODEL.client.close()
        SUMMARY_MODEL.client.close()
        return {
            "question": question,
            "answer": answer,
            "citations": citations,
        }

query=input('Please enter your query:')
rag=GNQNA_RAG(
    corpus_path=CORPUS_PATH,
    rag_template=RAG_TEMPLATE,
    retriever_template=RETRIEVER_TEMPLATE,
    summary_template=SUMMARY_TEMPLATE,
    )
output=rag.ask_question(query)
print(output['answer'])
