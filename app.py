return {
    "status": "ok" if total > 0 else "degraded",
    "chunks": total,
    "llm_configured": configured,
    "model": rag.OPENAI_MODEL if configured else None,
    "mode": "llm" if configured else "local",
    "ready": total > 0,
}
