
import chromadb
import uuid
from typing import List, Dict, Any, Optional
from core_types import MemoryManagerProtocol, MemoryFragment, EmotionalValence
import numpy as np

class VectorDBMemoryManager(MemoryManagerProtocol):
    """ChromaDB istifadə edərək yaddaşı idarə edir."""
    def __init__(self, path: str = "./memory_db"):
        self.client = chromadb.PersistentClient(path=path)
        # Hər istifadəçi üçün ayrı kolleksiya saxlamaq daha yaxşı praktikadır.
        # Amma sadəlik üçün hələlik bir ümumi kolleksiya istifadə edək.
        self.collection = self.client.get_or_create_collection(
            name="resonance_memories_v2",
            metadata={"hnsw:space": "cosine"} # dot product üçün "ip", L2 üçün "l2"
        )
        print(f"✅ Yaddaş Meneceri (ChromaDB) başladıldı. Verilənlər bazası: {path}")

    async def store_memory(self, user_id: str, memory: MemoryFragment) -> str:
        """Yaddaş fraqmentini vektor verilənlər bazasında saxlayır."""
        print(f"💾 '{memory.id}' ID-li yaddaş saxlanılır (İstifadəçi: {user_id})...")
        
        # ChromaDB-yə yalnız string, int, float, bool tipləri verilə bilər.
        # Get the serializable dictionary from the MemoryFragment
        serializable_metadata = memory.to_dict()

        # Embedding-i ayrıca idarə edirik. to_dict artıq onu metadatadan çıxarır,
        # buna görə əvvəlcə memory obyektindən götürürük və list formatına salırıq.
        embedding_list = None
        if memory.embedding is not None:
            embedding_list = memory.embedding.tolist() if isinstance(memory.embedding, np.ndarray) else memory.embedding
        # Əgər hər hansı səbəbdən embedding to_dict-dən geri qayıdarsa, onu da nəzərə alırıq
        embedded_from_meta = serializable_metadata.pop("embedding", None)
        if embedding_list is None and embedded_from_meta is not None:
            embedding_list = embedded_from_meta.tolist() if isinstance(embedded_from_meta, np.ndarray) else embedded_from_meta

        # Add user_id to metadata for filtering
        serializable_metadata["user_id"] = user_id

        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding_list] if embedding_list else None,
            metadatas=[serializable_metadata]
        )
        return memory.id

    async def retrieve_memories(self, user_id: str, query_embedding: Optional[np.ndarray] = None, limit: int = 5) -> List[MemoryFragment]:
        """Verilmiş embedding-ə ən oxşar yaddaşları tapır."""
        if query_embedding is None:
            print("⚠️ Axtarış üçün embedding verilməyib, boş siyahı qaytarılır.")
            return []
            
        print(f"🔍 İstifadəçi '{user_id}' üçün ən oxşar {limit} yaddaş axtarılır...")
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit,
            where={"user_id": user_id} # Yalnız bu istifadəçinin yaddaşları arasında axtar
        )
        
        retrieved_fragments = []
        if results and results['metadatas'] and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                # Metadata-dan user_id-ni silirik ki, from_dict xəta verməsin
                metadata.pop("user_id", None)
                # core_types.py-dəki dəyişikliklər sayəsində artıq manual JSON parsing-ə ehtiyac yoxdur.
                # ChromaDB metadatanı düzgün Python tipləri ilə qaytarır.
                retrieved_fragments.append(MemoryFragment.from_dict(metadata))
        
        print(f"✅ {len(retrieved_fragments)} yaddaş fraqmenti tapıldı.")
        return retrieved_fragments

    async def update_memory(self, user_id: str, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Yaddaşı yeniləyir (köhnəni silib, yenisini əlavə edir)."""
        print(f"🔄 '{memory_id}' ID-li yaddaş yenilənir...")
        try:
            # Əvvəlcə köhnə yaddaşı alırıq
            existing_data = self.collection.get(ids=[memory_id], where={"user_id": user_id})
            if not existing_data or not existing_data['metadatas']:
                print(f"❌ Yeniləmək üçün '{memory_id}' ID-li yaddaş tapılmadı.")
                return False

            memory_dict = existing_data['metadatas'][0]
            memory_dict.update(updates)
            
            # Yeni yaddaş obyektini yaradırıq
            updated_fragment = MemoryFragment.from_dict(memory_dict)
            
            # Köhnəni silib, yenisini əlavə edirik (ChromaDB-də bu "upsert" adlanır)
            self.collection.upsert(
                ids=[updated_fragment.id],
                embeddings=[updated_fragment.embedding.tolist() if updated_fragment.embedding is not None else None],
                metadatas=[updated_fragment.to_dict()]
            )
            print(f"✅ '{memory_id}' ID-li yaddaş uğurla yeniləndi.")
            return True
        except Exception as e:
            print(f"❌ Yaddaş yenilənərkən xəta baş verdi: {e}")
            return False
