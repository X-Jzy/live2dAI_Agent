import time
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np

client = QdrantClient(host="localhost", port=6333)

# 使用 sentence-transformers 生成文本嵌入，括号内模型可上huggingface寻找替换
model = SentenceTransformer('shibing624/text2vec-base-chinese')

def store_chat(input:str):
    embeddings = model.encode(input, convert_to_numpy=True)
    point=[]
    point.append(PointStruct(id=str(uuid.uuid4()), vector=embeddings.tolist(), payload={"text": input,"time":time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}))
    client.upsert(collection_name="live2d_ai", points=point)

def rag_search(input:str):
    q_emb = model.encode(input, convert_to_numpy=True).tolist()
    hits = client.search(collection_name="live2d_ai", query_vector=q_emb, limit=5)
    texts=[]
    print("\n检索结果：")
    for hit in hits:
        # hit 可能是 ScoredPoint，有 .payload 和 .score 属性
        payload = getattr(hit, 'payload', None) or hit
        score = getattr(hit, 'score', None)
        text = payload.get('text') if isinstance(payload, dict) else payload.payload.get('text')
        texts.append(text)
        print(f"score={score:.4f}\t{text}")
    return texts