"""
This scripts runs through a demo on the use of RAG system for genomic analysis

Reasoning based on tree-of-thought

Embedding model = Qwen/Qwen3-Embedding-0.6B

Generative model = calme-3.2-instruct-78b-Q4_K_S

Summary model = Phi-3-mini-4k-instruct-fp16

Requirements: langchain, llama-cpp-python (see tapas_env for full details)
"""


# Load document and process

texts =''

with open('../prelim_project/corpus.txt') as file:

    read = file.read()

    texts = texts + read


sentences = texts.split('\n')[:100000]

print('\nDocument ready!')


# Load quantized version of the generative model

from langchain_community.llms import LlamaCpp

gener_model = LlamaCpp(
    model_path = '../pretrained_models/calme-3.2-instruct-78b-Q4_K_S.gguf',
    max_tokens = 1000,
    n_ctx = 32768,
    seed = 2025,
    temperature = 0,
    verbose = False)


print('\nGenerative model loaded!')


# Load embedding model from hugging face

from langchain_community.embeddings import HuggingFaceEmbeddings

embed_model = HuggingFaceEmbeddings(
    model_name = 'Qwen/Qwen3-Embedding-0.6B')


print('\nEmbedding model loaded!')


# Set up or load vector database using embedding model for dense retrieval

from langchain_community.vectorstores import Chroma

import os

from tqdm import tqdm


db_path = '/tmp/chroma_db'


def build_load_db(sentences, embed_model, db_path = db_path, chunk_size=500):

	if os.path.exists(db_path):

		print('\nLoading Chroma vector database from disk...')

		db = Chroma(
			persist_directory=db_path,
			embedding_function=embed_model)

		return db

	else:

		print('\nBuilding Chroma vector database and saving to disk...')

		for i in tqdm(range(0, len(sentences), chunk_size)):

			chunk = sentences[i:i+chunk_size]

			db = Chroma.from_texts(
				texts = chunk,
				embedding=embed_model,
				persist_directory=db_path)
			db.persist()

		return db



db = build_load_db(sentences, embed_model)

print('\nAccess to vector database confirmed!')



# Set up sparse retriever

from langchain_community.retrievers import BM25Retriever

from langchain.retrievers.ensemble import EnsembleRetriever


bm25_retriever = BM25Retriever.from_texts(sentences)

bm25_retriever.k = 20 # define number of documents to retrieve



# Combine dense and sparse retrievers

ensemble_retriever = EnsembleRetriever(
	retrievers=[db.as_retriever(), bm25_retriever],
	weights=[0.3, 0.7])



# Set up RAG prompt

from langchain_core.prompts import PromptTemplate

rag_template = """
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

rag_prompt = PromptTemplate(
    input_variables = ['context', 'question', 'summary'],
    template = rag_template)


# Set up retriever prompt

retriever_template = """
<s><|user|>
Given the following conversation, generate a search query to retrieve relevant documents. 

Conversation:
{input}
<|end|>
<|assistant|>
"""


retriever_prompt = PromptTemplate(
	input_variables = ['input'],
	template =retriever_template)


# Set up summary prompt for memory propagation

summary_template = """
<s><|user|>

Summarize the conversations and update with the new lines. Be as concise as possible without loosing key information.

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:<|end|>
<|assistant|>
"""

summary_prompt = PromptTemplate(
    input_variables = ['summary', 'new_lines'], 
    template = summary_template)



# Perform conversation summary using a smaller model (Phi-3)

summary_model = LlamaCpp(
    model_path = '../pretrained_models/Phi-3-mini-4k-instruct-fp16.gguf',
    max_tokens = 500,
    n_ctx = 4096,
    seed = 2025,
    temperature = 0,
    verbose = False)

from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(
    llm = summary_model,
    memory_key = 'chat_history',
    input_key = 'input',
    output_key = 'answer',
    prompt = summary_prompt,
    max_token_limit = 1000,
    return_messages = True)




# Define RAG pipeline


from langchain.chains.history_aware_retriever import create_history_aware_retriever


history_aware_retriever = create_history_aware_retriever(
	retriever = ensemble_retriever,
	llm = gener_model,
	prompt = retriever_prompt)


from langchain.chains.combine_documents import create_stuff_documents_chain

combine_docs_chain = create_stuff_documents_chain(
	llm = gener_model,
	prompt = rag_prompt)


from langchain.chains.retrieval import create_retrieval_chain

retrieval_chain = create_retrieval_chain(
    combine_docs_chain = combine_docs_chain,
    retriever = history_aware_retriever)

print('\nPipeline ready!')


# Get generated answer and citations


def rag(question, retrieval_chain = retrieval_chain, memory = memory):

	print('\nQuery execution...')

	# Get memory content

	memory_var = memory.load_memory_variables({})

	chat_history = memory_var.get('chat_history', '')

	# Execute query

	result = retrieval_chain.invoke(
		{'input': question,
		'chat_history': chat_history})

	print('\nQuestion: ', question)

	print('\n Generated_text:\n', result['answer'])

	print('\n Citations:\n', result['context'])

	# Update memory

	memory.save_context(
		{'input': question},
		{'answer': result['answer']})



rag('Two traits have similar lod values at a specific position when the computation of the difference between the lod values gives a result less or equal to 0.5. Using that information, identify 2 traits that have similar lod values on chromosome 1 position 3010274. If any pair of traits does not have similar lod values at that position, try another pair until you exhaust all the possibilities.')
