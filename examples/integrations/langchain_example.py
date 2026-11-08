"""Optional LangChain example; set OPENAI_API_KEY before running the chain."""

import os


def build_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY before invoking the hosted-model chain")
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Answer only from the supplied evidence. Say when it is missing."),
            ("human", "Question: {question}\nEvidence: {evidence}"),
        ]
    )
    return prompt | ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini")) | StrOutputParser()
