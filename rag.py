"""
rag.py - Retrieval-Augmented Generation engine for the MIET chatbot.
====================================================================
Project : AI-Powered MIET Jammu Website Chatbot (BTech Semester Project)

Pipeline for every question:
  1. RETRIEVE  - score every knowledge-base chunk against the question
                 using a small, dependency-free TF-IDF cosine retriever
                 (SQLite stores the chunks; see database.py).
  2. GENERATE  - if OPENAI_API_KEY is configured, send the retrieved
                 chunks + question to the LLM with strict grounding
                 instructions. If no key (or the API fails), build an
                 EXTRACTIVE answer directly from the retrieved chunks,
                 so the bot still gives real, specific, sourced answers.
  3. CITE      - always return the source URLs of the chunks used.
  4. BE HONEST - if nothing relevant is retrieved, say so clearly and
                 point to the official website instead of inventing
                 college information.

An optional ChromaDB upgrade path is documented in README.md; the
default build keeps retrieval beginner-friendly and dependency-light.
"""

import math
import os
import re
from collections import Counter

from dotenv import load_dotenv

import database

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Words too common to help with matching.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "do", "does",
    "did", "can", "could", "will", "would", "should", "i", "you", "we", "they",
    "he", "she", "it", "of", "in", "on", "at", "to", "for", "from", "with",
    "about", "and", "or", "but", "not", "no", "yes", "what", "which", "who",
    "whom", "when", "where", "how", "why", "me", "my", "your", "our", "their",
    "there", "this", "that", "these", "those", "please", "tell", "know",
    "miet", "jammu", "college", "institute",  # appear everywhere -> no signal
}

# Tiny synonym map so student phrasing matches website wording.
SYNONYMS = {
    "fee": ["fees", "fee", "cost", "tuition", "price", "charges"],
    "fees": ["fees", "fee", "cost", "tuition", "price", "charges"],
    "cost": ["fees", "fee", "cost", "tuition", "price"],
    "admission": ["admission", "admissions", "apply", "application", "eligibility"],
    "apply": ["admission", "admissions", "apply", "application"],
    "placement": ["placement", "placements", "recruiters", "jobs", "career"],
    "job": ["placement", "placements", "recruiters", "jobs", "career"],
    "exam": ["exam", "exams", "examination", "examinations", "datesheet", "timetable"],
    "timetable": ["timetable", "schedule", "calendar", "datesheet"],
    "sports": ["sports", "basketball", "cricket", "futsal", "recreational"],
    "hostel": ["hostel", "accommodation", "residence"],
    "course": ["course", "courses", "program", "programs", "programme", "btech", "degree"],
    "branch": ["branch", "branches", "department", "departments", "program"],
    "notice": ["notice", "notices", "circular", "announcement", "induction"],
    "event": ["event", "events", "fest", "activities", "competition"],
    "contact": ["contact", "phone", "email", "address", "location"],
}


def tokenize(text: str) -> list[str]:
    """Lowercase, split into words, drop stopwords, expand synonyms."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    tokens: list[str] = []
    for w in words:
        if w in STOPWORDS:
            continue
        tokens.append(w)
        if w in SYNONYMS:
            tokens.extend(SYNONYMS[w])
    return tokens


class Retriever:
    """A small in-memory TF-IDF retriever over the SQLite chunks."""

    def __init__(self) -> None:
        self.chunks: list[dict] = []
        self.doc_tokens: list[Counter] = []
        self.idf: dict[str, float] = {}
        self.refresh()

    def refresh(self) -> None:
        """(Re)load chunks from SQLite and rebuild TF-IDF statistics."""
        database.seed_if_empty()
        self.chunks = database.get_all_chunks()
        self.doc_tokens = [
            Counter(tokenize(c["title"] + " " + c["content"])) for c in self.chunks
        ]
        n_docs = max(len(self.chunks), 1)
        df: Counter = Counter()
        for tok in self.doc_tokens:
            df.update(tok.keys())
        self.idf = {t: math.log((n_docs + 1) / (dfc + 1)) + 1.0 for t, dfc in df.items()}

    def _vector(self, counts: Counter) -> dict[str, float]:
        return {t: c * self.idf.get(t, 1.0) for t, c in counts.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def retrieve(self, question: str, k: int = 3) -> list[dict]:
        """Return up to k chunks scored above a relevance threshold."""
        q_vec = self._vector(Counter(tokenize(question)))
        scored = []
        for chunk, tok in zip(self.chunks, self.doc_tokens):
            score = self._cosine(q_vec, self._vector(tok))
            if score > 0.06:  # relevance threshold -> honesty about misses
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [dict(c, score=round(s, 3)) for s, c in scored[:k]]


# ----------------------------------------------------------------------
# Answer generation
# ----------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are the official AI assistant for MIET Jammu (Model Institute of "
    "Engineering and Technology, Jammu). Answer the student's question using "
    "ONLY the context passages provided. If the context does not contain the "
    "answer, say honestly that the information is not in your knowledge base "
    "and advise checking https://mietjmu.in/ or the college office. Never "
    "invent fees, dates, names or official details. Keep answers concise, "
    "friendly and formatted for students."
)

NOT_FOUND_ANSWER = (
    "I could not find reliable information about that in my MIET knowledge "
    "base, and I don't want to guess about official college details. Please "
    "check the official website https://mietjmu.in/ or contact the college "
    "office directly. You can also try asking me about admissions, programs, "
    "certification program fees, placements, sports facilities, notices or "
    "recent events."
)


def _extractive_answer(question: str, hits: list[dict]) -> str:
    """Compose a grounded answer directly from retrieved chunk text
    (used when no LLM key is configured, or the API call fails)."""
    q_tokens = set(tokenize(question))
    parts: list[str] = []
    for hit in hits[:2]:
        sentences = re.split(r"(?<=[.!?])\s+", hit["content"])
        picked = [s for s in sentences if q_tokens & set(tokenize(s))]
        snippet = " ".join(picked[:4]) if picked else " ".join(sentences[:3])
        parts.append(f"**{hit['title']}** — {snippet}")
    header = "Here is what I found in the MIET knowledge base:\n\n"
    return header + "\n\n".join(parts)


def _llm_answer(question: str, hits: list[dict]) -> str:
    """Ask the configured OpenAI model, grounded in the retrieved chunks."""
    from openai import OpenAI  # imported lazily so the app runs without it

    context = "\n\n".join(
        f"[Source: {h['title']} | {h['url']}]\n{h['content']}" for h in hits
    )
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        max_tokens=450,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context passages:\n{context}\n\nStudent question: {question}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


def answer_question(question: str, retriever: Retriever) -> dict:
    """Full RAG pipeline. Always returns a dict the API can serialize."""
    question = (question or "").strip()
    if not question:
        return {
            "answer": "Please type a question about MIET Jammu.",
            "sources": [],
            "mode": "validation",
        }

    hits = retriever.retrieve(question)

    # Honest handling of missing information.
    if not hits:
        return {"answer": NOT_FOUND_ANSWER, "sources": [], "mode": "not_found"}

    sources = []
    seen = set()
    for h in hits:
        key = (h["title"], h["url"])
        if key not in seen:
            seen.add(key)
            sources.append({"title": h["title"], "url": h["url"]})

    if OPENAI_API_KEY:
        try:
            return {
                "answer": _llm_answer(question, hits),
                "sources": sources,
                "mode": "llm",
            }
        except Exception as exc:  # API error -> graceful, still grounded
            print(f"[rag] LLM call failed ({exc.__class__.__name__}): {exc}")
            return {
                "answer": _extractive_answer(question, hits)
                + "\n\n_(Note: the AI generation service was unavailable, so this "
                "answer was extracted directly from the official sources below.)_",
                "sources": sources,
                "mode": "extractive_fallback",
            }

    return {
        "answer": _extractive_answer(question, hits),
        "sources": sources,
        "mode": "extractive",
    }
