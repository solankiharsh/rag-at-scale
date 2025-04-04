# Description: This file contains the code for the semantic chunking strategy and code generation.
# The semantic chunking strategy is a process to split text into meaningful chunks
# while maintaining the semantic meaning of the text.
# The code generation part generates Python code based on the strategy provided
# to split the text into chunks.
# The `semantic_chunking` function uses the generated code to split the text into chunks
# and returns the result.
# The `cut_text` function is used to cut the text into smaller parts
# if it exceeds a certain word count.
# The `semantic_chunking_strategy` function generates a strategy for splitting the text
# based on the input text.
# The `semantic_chunking_strategy_code` function generates Python code based on the strategy
# provided to split the text into chunks.
# The `semantic_chunking_code` function combines the above functions to generate the code
# for splitting the text into chunks.
# The `semantic_chunking` function uses the generated code to split the text into chunks
# and returns the result.
# The code uses the OpenAI API for text generation and completion.
# The `RagDocument` class is used to represent the document content and metadata.
# The code is designed to be used as part of the RecursiveChunker class in the RAG framework.
import openai

from config import Config
from src.Shared.RagDocument import RagDocument

config = Config()


def get_openai_api_key():
    return config.openai_api_key


def semantic_chunking_strategy(text: str) -> dict:
    messages = []
    messages = [
        {
            "role": "system",
            "content": (
                "You are helpful assistant"
                + "Based on a given piece of text provided, describe the correct strategy to split "
                + " the text. Describe the schema you would follow to chunk the text."
                + "Describe the schema you would follow to chunk the text."
                + "Be concise, but specific the process to allow a developer to implement it."
                + "The goal is for the chunks to maintain the semantic meaning of the text."
                + "For example, if I have a text that has several questions and answers, "
                + "they should be kept together inside the same chunk."
                + "If I have a text that has many paragraphs, ideally try to keep paragraphs "
                + "within the same chunk."
                + "Same applies for sentences, try to keep them together within the same chunk "
                + "and not cut in the middle."
            ),
        },
        {"role": "user", "content": text},
    ]
    client = openai.OpenAI(api_key=get_openai_api_key())
    response = client.chat.completions.create(
        model="gpt-4-0613", messages=messages, temperature=0.9
    )
    response_message = response.choices[0].message
    return {"content": response_message.content}


def semantic_chunking_strategy_code(text: str, chunking_strategy: str) -> dict:
    messages = []
    messages = [
        {
            "role": "system",
            "content": (
                "You are helpful developer that writes python code."
                + "Output the code in this format: ```python def split_text_into_chunks(text): "
                + "<Insert Code>```"
                + "The function `split_text_into_chunks` should output an array of text chunks."
                + "Implement the strategy provided by the user to help split text."
            ),
        },
        {"role": "user", "content": chunking_strategy},
    ]
    # Use openai.OpenAI directly but configure API key from config
    client = openai.OpenAI(api_key=get_openai_api_key())
    response = client.chat.completions.create(
        model="gpt-4-0613", messages=messages, temperature=0.9
    )
    response_message = response.choices[0].message
    return {"content": response_message.content}


def semantic_chunking_code(text: str) -> str:
    fixed_text = cut_text(text)
    chunking_strategy_response = semantic_chunking_strategy(text=fixed_text)
    chunking_strategy = chunking_strategy_response["content"]

    chunking_code_response = semantic_chunking_strategy_code(
        text=fixed_text, chunking_strategy=chunking_strategy
    )
    chunking_code = chunking_code_response["content"]
    chunking_code_exec = chunking_code.split("`python")[1].split("`")[0]
    return chunking_code_exec


def semantic_chunking(documents: list[RagDocument], chunking_code_exec: str) -> list[RagDocument]:
    exec(chunking_code_exec, globals())
    result_doc = []
    for doc in documents:
        results = split_text_into_chunks(doc.content)  # noqa: F821
        for result in results:
            result_doc.append(RagDocument(id=doc.id, content=result, metadata=doc.metadata))
    return result_doc


def cut_text(s):
    words = s.split()  # Split the string into a list of words
    word_count = len(words)

    if word_count <= 750:
        return s  # If the string is less than or equal to 750 words, return the entire string

    if word_count > 750:
        if word_count >= 1250:  # Check if we can skip 500 and still get 750
            return " ".join(words[500:1250])  # Skip the first 500 words and take the next 750 words
        else:
            return " ".join(words[word_count - 750 : word_count])  # Take the last 750 words
