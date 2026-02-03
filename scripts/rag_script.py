"""
This scripts runs through a demo on the use of RAG system for genomic analysis

Reasoning based on tree-of-thought

Embedding model = Qwen/Qwen3-Embedding-0.6B

Generative model = calme-3.2-instruct-78b-Q4_K_S

Summary model = Phi-3-mini-4k-instruct-fp16

Requirements: langchain, llama-cpp-python (see tapas_env for full details)


python rag_script.py <corpus-text.txt> <generative-model.gguf>
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

from tqdm import tqdm


CORPUS_TEXT = "/home/bonfacem/models/corpus.txt"
# XXX: Can we pickle this to make load times faster?
# XXX: Remove hard-coded paths.

GENERATIVE_MODEL = LlamaCpp(
    model_path="/home/bonfacem/models/calme-3.2-instruct-78b-Q4_K_S.gguf",
    max_tokens=1_000,
    n_ctx=32_768,
    seed=2_025,
    temperature=0,
    verbose=False)

# XXX: Can we pickle this to make load times faster?
# XXX: Remove hard-coded paths.
SUMMARY_MODEL = LlamaCpp(
    model_path='/home/bonfacem/models/Phi-3-mini-4k-instruct-fp16.gguf',
    max_tokens=500,
    n_ctx=4096,
    seed=2025,
    temperature=0,
    verbose=False)


# Our templates for our simple RAG system
RAG_TEMPLATE = """
<s><|user|>

Relevant information:
{context}

History:
{chat_history}

Provide a concise answer to the question below. Check first in the history above. If you do not find the answer to the question, use the relevant information above. Do not add any external information.

Explore different reasoning by emulating a conversation between 3 experts. All experts will write down 1 step of their thinking, then share with the group. Then all experts will go on to the next step and so on. If any expert realizes his wrong at any point, he should leave the conversation.

The question is:
{input}
<|end|>
<|assistant|>
"""

RETRIEVER_TEMPLATE = """
<s><|user|>
Given the following conversation, generate a search query to retrieve relevant documents.

Conversation:
{input}
<|end|>
<|assistant|>
"""

SUMMARY_TEMPLATE = """
<s><|user|>

Summarize the conversations and update with the new lines. Be as concise as possible without loosing key information.

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:<|end|>
<|assistant|>
"""


def corpus_to_sentences(file_path: str) -> list:
    """Convert a corpus into an array of sentences.

    KLUDGE: XXXX: Corpus of text should be RDF eventually.  This here
    is for testing.

    """
    if not Path(file_path).exists():
        sys.exit(1)
    with open(file_path, "r", encoding="utf-8") as stream:
        return stream.read().split("\n")[:100_000]


@dataclass
class GNQNA_RAG():
    corpus: str
    rag_template: str
    retriever_template: str
    summary_template: str
    memory: Any = field(init=False)
    retrieval_chain: Any = field(init=False)
    ensemble_retriever: Any = field(init=False)
    sentences: list = field(init=False)
    rag_prompt: Any = field(init=False)
    retriever_prompt: Any = field(init=False)
    summary_prompt: Any = field(init=False)
    chroma_db: Any = field(init=False)

    def __post_init__(self):
        self.sentences = corpus_to_sentences(self.corpus)
        self.chroma_db = self.set_chroma_db(
            sentences=self.sentences,
            embed_model=HuggingFaceEmbeddings(
                model_name="Qwen/Qwen3-Embedding-0.6B"),
            db_path='/home/bonfacem/tmp/chroma_db'
        )

        # Init'ing the ensemble retriever
        bm25_retriever = BM25Retriever.from_texts(self.sentences)
        bm25_retriever.k = 20   # KLUDGE: Explain why the magic number 20
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.chroma_db.as_retriever(), bm25_retriever],
            weights=[0.3, 0.7])  # KLUDGE: Explain why the magic array

        # Init'ing the prompts
        self.rag_prompt = PromptTemplate(
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
        self.memory = ConversationSummaryBufferMemory(
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

    def set_chroma_db(self, sentences: list,
                      embed_model: Any, db_path: str,
                      chunk_size: int = 500) -> Any:
        match Path(db_path).exists():
            case True:
                db = Chroma(
                    persist_directory=db_path,
                    embedding_function=embed_model
                )
                return db
            case _:
                for i in tqdm(range(0, len(sentences), chunk_size)):
                    chunk = sentences[i:i+chunk_size]
                    db = Chroma.from_texts(
                        texts=chunk,
                        embedding=embed_model,
                        persist_directory=db_path)
                    db.persist()
                return db

    def ask_question(self, question: str):
        memory_var = self.memory.load_memory_variables({})
        chat_history = memory_var.get('chat_history', '')
        result = self.retrieval_chain.invoke(
            {'input': question,
             'chat_history': chat_history})
        answer = result.get("answer")
        citations = result.get("context")
        self.memory.save_context(
            {'input': question},
            {'answer': answer})
        return {
            "question": question,
            "answer": answer,
            "citations": citations,
        }


rag = GNQNA_RAG(
    corpus=CORPUS_TEXT,
    rag_template=RAG_TEMPLATE,
    retriever_template=RETRIEVER_TEMPLATE,
    summary_template=SUMMARY_TEMPLATE,
)


answer = rag.ask_question("Two traits have similar lod values at a specific position when the computation of the difference between the lod values gives a result less or equal to 0.5. Using that information, identify 2 traits that have similar lod values on chromosome 1 position 3010274. If any pair of traits does not have similar lod values at that position, try another pair until you exhaust all the possibilities.")

print(answer)
