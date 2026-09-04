"""
ChromaDB Vector Store Integration
Embeds and indexes:
1. RM unstructured notes (keyed by client_id, note_id, author)
2. World event log entries (keyed by event_date, region, severity)
3. Investment mandate clauses and guidelines
Enables semantic search, contextual retrieval, and client nuance matching.
"""

import os
import json
import chromadb
from typing import List, Dict, Any, Optional
from src.data_layer import WealthDataRepository

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

class WealthVectorStore:
    _instance = None

    def __init__(self, chroma_dir: str = CHROMA_DIR):
        self.chroma_dir = chroma_dir
        os.makedirs(self.chroma_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.repo = WealthDataRepository.get_instance()
        
        self.notes_collection = self.client.get_or_create_collection(
            name="rm_notes",
            metadata={"description": "Unstructured RM meeting and call notes"}
        )
        self.events_collection = self.client.get_or_create_collection(
            name="market_events",
            metadata={"description": "2026 World events log and shock transmission channels"}
        )
        self.mandates_collection = self.client.get_or_create_collection(
            name="mandate_rules",
            metadata={"description": "Mandate codes, allocation rules and concentration limits"}
        )
        self.index_data()

    @classmethod
    def get_instance(cls) -> "WealthVectorStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def index_data(self):
        """Indexes notes, events, and mandates into ChromaDB."""
        # 1. Index RM Notes
        if self.notes_collection.count() == 0:
            notes = self.repo.rm_notes_data
            if notes:
                ids = [n.get("note_id", f"note_{i}") for i, n in enumerate(notes)]
                documents = [n.get("note", "") for n in notes]
                metadatas = [
                    {
                        "client_id": n.get("client_id", ""),
                        "note_date": n.get("note_date", ""),
                        "rm_name": n.get("rm_name", ""),
                        "channel": n.get("channel", "")
                    }
                    for n in notes
                ]
                self.notes_collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )

        # 2. Index Events
        if self.events_collection.count() == 0:
            events = self.repo.get_events()
            if events:
                ids = [f"event_{i}" for i in range(len(events))]
                docs = [f"{e.get('event_type')}: {e.get('description')} ({e.get('region')}) Transmission: {e.get('primary_transmission')}" for e in events]
                metas = [
                    {
                        "event_date": str(e.get("event_date", "")),
                        "severity": str(e.get("severity", "")),
                        "region": str(e.get("region", ""))
                    }
                    for e in events
                ]
                self.events_collection.add(ids=ids, documents=docs, metadatas=metas)

    def search_rm_notes(self, query: str, client_id: Optional[str] = None, n_results: int = 3) -> List[Dict[str, Any]]:
        """Semantic search across RM notes with optional client_id filter."""
        where_filter = {"client_id": client_id} if client_id else None
        results = self.notes_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        hits = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else []
            ids = results["ids"][0] if results["ids"] else []
            for doc, meta, doc_id in zip(docs, metas, ids):
                hits.append({
                    "id": doc_id,
                    "text": doc,
                    "client_id": meta.get("client_id"),
                    "note_date": meta.get("note_date"),
                    "rm_name": meta.get("rm_name"),
                    "channel": meta.get("channel")
                })
        return hits

    def search_events(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Semantic search across market shock events."""
        results = self.events_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        hits = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else []
            ids = results["ids"][0] if results["ids"] else []
            for doc, meta, doc_id in zip(docs, metas, ids):
                hits.append({
                    "id": doc_id,
                    "text": doc,
                    "date": meta.get("event_date"),
                    "severity": meta.get("severity"),
                    "region": meta.get("region")
                })
        return hits
