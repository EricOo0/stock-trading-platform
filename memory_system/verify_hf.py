import sys
import os
import time

# 添加项目根目录到 Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 强制设置环境变量为 huggingface
os.environ["EMBEDDING_PROVIDER"] = "huggingface"

# 重新加载 settings
from memory_system.config import settings
print(f"🔹 EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
print(f"🔹 HF_EMBEDDING_MODEL: {settings.HF_EMBEDDING_MODEL}")

from memory_system.utils.embeddings import EmbeddingService

def verify_hf():
    print("🚀 Starting HuggingFace Embedding verification...")
    
    start_time = time.time()
    service = EmbeddingService()
    init_time = time.time()
    print(f"✓ Service initialized in {init_time - start_time:.2f}s")
    
    texts = ["Hello world", "This is a test sentence for embeddings"]
    print(f"\n📝 Generating embeddings for {len(texts)} documents...")
    embeddings = service.embed_documents(texts)
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    if embeddings:
        print(f"  Dimension: {len(embeddings[0])}")
        assert len(embeddings[0]) == 384, f"Expected 384 dimensions for all-MiniLM-L6-v2, got {len(embeddings[0])}"
    
    print("\n🔍 Generating query embedding...")
    query_emb = service.embed_query("search query")
    print(f"✓ Query embedding generated. Dimension: {len(query_emb)}")
    
    print("\n✅ Verification Completed Successfully!")

if __name__ == "__main__":
    verify_hf()
