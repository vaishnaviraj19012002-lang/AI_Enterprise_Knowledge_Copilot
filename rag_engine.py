import os
import numpy as np

from google import genai
from google.genai import types


class RAGEngine:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in .env"
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.embedding_model = "gemini-embedding-001"
        self.generation_model = "gemini-3.6-flash"

        self.embeddings = []
        self.documents = []

    def create_embeddings(self, texts):

        result = self.client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )

        return np.array(
            [embedding.values for embedding in result.embeddings],
            dtype="float32"
        )

    def add_documents(self, chunks):

        if not chunks:
            return

        texts = [
            item["text"]
            for item in chunks
        ]

        embeddings = self.create_embeddings(texts)

        norms = np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True
        )

        embeddings = embeddings / (
            norms + 1e-10
        )

        self.embeddings.extend(
            embeddings
        )

        self.documents.extend(
            chunks
        )

    def search(
        self,
        query,
        top_k=5
    ):

        if not self.embeddings:
            return []

        result = self.client.models.embed_content(
            model=self.embedding_model,
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )

        query_embedding = np.array(
            result.embeddings[0].values,
            dtype="float32"
        )

        query_embedding = (
            query_embedding /
            (np.linalg.norm(query_embedding) + 1e-10)
        )

        document_embeddings = np.array(
            self.embeddings
        )

        scores = (
            document_embeddings
            @ query_embedding
        )

        top_indices = np.argsort(
            scores
        )[::-1][:top_k]

        results = []

        for index in top_indices:

            document = self.documents[
                index
            ].copy()

            document["score"] = float(
                scores[index]
            )

            results.append(
                document
            )

        return results

    def generate_answer(
        self,
        question,
        retrieved_documents,
        chat_history=None
    ):

        if not retrieved_documents:

            return (
                "The information was not found "
                "in the uploaded documents."
            )

        context_parts = []

        for i, document in enumerate(
            retrieved_documents,
            start=1
        ):

            context_parts.append(
                f"""
SOURCE {i}

Document:
{document["source"]}

Chunk:
{document["chunk_id"]}

Content:
{document["text"]}
"""
            )

        context = "\n".join(
            context_parts
        )

        history_text = ""

        if chat_history:

            for message in chat_history[-8:]:

                history_text += (
                    f'{message["role"]}: '
                    f'{message["content"]}\n'
                )

        prompt = f"""
You are an Enterprise Knowledge Copilot.

Your job is to answer employee questions using
the uploaded enterprise documents.

IMPORTANT CONVERSATION RULES:

1. Use the conversation history to understand
   follow-up questions and references such as:
   "them", "it", "that", "those", "all of them",
   "the above", and similar phrases.

2. The latest employee question is the question
   you must answer.

3. Conversation history provides context only.
   Enterprise documents are the source of truth.

4. Do NOT repeat an earlier answer just because
   the new question is related to it.

5. If the latest question asks for information
   that is not explicitly available in the documents,
   say:
   "The information was not found in the uploaded documents."

6. Do not invent or assume company policies.

7. Keep the answer professional and concise.

8. Include a source reference when the answer
   comes from the uploaded documents.

9. Clearly distinguish documented facts from
   recommendations or interpretations.

CONVERSATION HISTORY:

{history_text}

RETRIEVED DOCUMENTS:

{context}

LATEST EMPLOYEE QUESTION:

{question}

ANSWER:
"""

        response = self.client.models.generate_content(
            model=self.generation_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )

        return response.text