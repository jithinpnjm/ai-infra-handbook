import json

PROMPT_TEMPLATE = """You are a documentation assistant. Answer the question
based only on the context below. If the answer is not in the context,
say "I don't know" rather than making it up.

Context:
{context}

Question: {question}

Answer:"""

def assemble(question: str, chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(chunks)
    return PROMPT_TEMPLATE.format(context=context, question=question)
