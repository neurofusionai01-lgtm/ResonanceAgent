
import asyncio
import chromadb
import uuid
from typing import List, Dict, Any, Optional
from core_types import MemoryManagerProtocol, MemoryFragment, EmotionalValence
import numpy as np

# A no-op embedding function to allow custom dimension embeddings
# without Chroma trying to re-calculate them using the default model.
from chromadb import Documents, EmbeddingFunction, Embeddings
class PassthroughEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        # We handle embeddings externally, so this just returns empty
        return []

class VectorDBMemoryManager(MemoryManagerProtocol):
    """ChromaDB istifadə edərək yaddaşı idarə edir."""
    def __init__(self, path: str = "./memory_db"):
        self.client = chromadb.PersistentClient(path=path)
        # Hər istifadəçi üçün ayrı kolleksiya saxlamaq daha yaxşı praktikadır.
        # Amma sadəlik üçün hələlik bir ümumi kolleksiya istifadə edək.

        # We explicitly use a passthrough embedding function to support custom dimensions (e.g., 768)
        # instead of Chroma's default 384-dim SentenceTransformer.
        self.collection = self.client.get_or_create_collection(
            name="resonance_memories_v2",
            metadata={"hnsw:space": "cosine"}, # dot product üçün "ip", L2 üçün "l2"
            embedding_function=PassthroughEmbeddingFunction()
        )
        print(f"✅ Yaddaş Meneceri (ChromaDB) başladıldı. Verilənlər bazası: {path}")

    async def store_memory(self, user_id: str, memory: MemoryFragment) -> str:
        """Yaddaş fraqmentini vektor verilənlər bazasında saxlayır."""
        print(f"💾 '{memory.id}' ID-li yaddaş saxlanılır (İstifadəçi: {user_id})...")
        
        # Embedding-in düzgün formatda olduğundan əmin oluruq
        embedding_list = None
        if memory.embedding is not None:
            if isinstance(memory.embedding, np.ndarray):
                embedding_list = memory.embedding.tolist()
            else:
                embedding_list = memory.embedding # Assume it's already a list

        # ChromaDB-yə yalnız string, int, float, bool tipləri verilə bilər.
        # Get the serializable dictionary from the MemoryFragment
        # Note: MemoryFragment.to_dict() already pops 'embedding' from the dict internally!
        serializable_metadata = memory.to_dict()

        # We need to rely on the embedding_list we prepared earlier from memory.embedding
        # because serializable_metadata won't have it.

        # However, let's verify if to_dict pops it. Yes, it does in core_types.py.
        # So we just rely on 'embedding_list' calculated at the start of this function.
        # But wait, the start of function set embedding_list from memory.embedding.

        # We need to ensure embedding_list is properly formatted.
        if embedding_list is not None and isinstance(embedding_list, np.ndarray):
            embedding_list = embedding_list.tolist()

        # Double check: if embedding was not popped in to_dict (if core_types changed), remove it now.
        if "embedding" in serializable_metadata:
             serializable_metadata.pop("embedding")

        # Add user_id to metadata for filtering
        serializable_metadata["user_id"] = user_id

        # Prepare document content (required by ChromaDB)
        document_content = f"Query: {memory.content.get('query', '')}\nResponse: {memory.content.get('response', '')}"

        # We must provide embeddings if we disabled the embedding function.
        # If we don't have embeddings, we can't add to Chroma if embedding_function is None?
        # Actually, Chroma requires embeddings if embedding_function is None.
        # But we might want to store memory without embedding (rare)?
        # If embedding_list is None, we should probably generate a dummy or fail?
        # But our system logic is: NLP generates embedding.

        await asyncio.to_thread(
            self.collection.add,
            ids=[memory.id],
            # Use strict list check. If embedding_list is None, this passes None,
            # which triggers 'Expected Embeddings to be non-empty' if function is None.
            # But wait, audit script provides embeddings!
            # Let's verify why audit script's embedding is failing.
            embeddings=[embedding_list] if embedding_list is not None else None,
            metadatas=[serializable_metadata],
            documents=[document_content]
        )
        return memory.id

    async def retrieve_memories(self, user_id: str, query_embedding: Optional[np.ndarray] = None, limit: int = 5) -> List[MemoryFragment]:
        """Verilmiş embedding-ə ən oxşar yaddaşları tapır."""
        if query_embedding is None:
            print("⚠️ Axtarış üçün embedding verilməyib, boş siyahı qaytarılır.")
            return []
            
        print(f"🔍 İstifadəçi '{user_id}' üçün ən oxşar {limit} yaddaş axtarılır...")
        
        results = await asyncio.to_thread(
            self.collection.query,
            query_embeddings=[query_embedding.tolist()],
            n_results=limit,
            where={"user_id": user_id}, # Yalnız bu istifadəçinin yaddaşları arasında axtar
            include=['metadatas', 'embeddings', 'documents', 'distances']
        )
        
        retrieved_fragments = []
        if results and results['metadatas'] and results['metadatas'][0]:
            # Iterate through metadatas and embeddings simultaneously
            metadatas = results['metadatas'][0]
            embeddings = results['embeddings'][0] if results['embeddings'] else [None] * len(metadatas)

            for i, metadata in enumerate(metadatas):
                # Metadata-dan user_id-ni silirik ki, from_dict xəta verməsin
                metadata.pop("user_id", None)

                # Reconstruct memory fragment
                fragment = MemoryFragment.from_dict(metadata)

                # Re-attach the embedding if it exists
                if embeddings[i] is not None:
                    fragment.embedding = np.array(embeddings[i])

                retrieved_fragments.append(fragment)
        
        print(f"✅ {len(retrieved_fragments)} yaddaş fraqmenti tapıldı.")
        return retrieved_fragments

    async def update_memory(self, user_id: str, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Yaddaşı yeniləyir (köhnəni silib, yenisini əlavə edir)."""
        print(f"🔄 '{memory_id}' ID-li yaddaş yenilənir...")
        try:
            # Əvvəlcə köhnə yaddaşı alırıq
            existing_data = await asyncio.to_thread(self.collection.get, ids=[memory_id], where={"user_id": user_id})
            if not existing_data or not existing_data['metadatas']:
                print(f"❌ Yeniləmək üçün '{memory_id}' ID-li yaddaş tapılmadı.")
                return False

            memory_dict = existing_data['metadatas'][0]
            memory_dict.update(updates)
            
            # Yeni yaddaş obyektini yaradırıq
            updated_fragment = MemoryFragment.from_dict(memory_dict)
            
            # Köhnəni silib, yenisini əlavə edirik (ChromaDB-də bu "upsert" adlanır)
            await asyncio.to_thread(
                self.collection.upsert,
                ids=[updated_fragment.id],
                embeddings=[updated_fragment.embedding.tolist() if updated_fragment.embedding is not None else None],
                metadatas=[updated_fragment.to_dict()]
            )
            print(f"✅ '{memory_id}' ID-li yaddaş uğurla yeniləndi.")
            return True
        except Exception as e:
            print(f"❌ Yaddaş yenilənərkən xəta baş verdi: {e}")
            return False
