from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

# 初始化嵌入模型（免费本地模型）
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 初始知识库内容（可扩展）
DEFAULT_KNOWLEDGE = [
    "注意力恢复理论（ART）指出：自然场景中柔和的动态光影、低色彩饱和度能有效降低焦虑水平。",
    "环境心理学研究表明：植物性景观（绿色植被、水流）对情绪有显著积极影响。",
    "数字疗愈中，色彩饱和度最优区间为 0.6-0.8，运动速度应控制在 0.3 倍速以下。",
    "依恋理论：在陪伴场景中，持续、可预期的温暖回应能增强安全感。",
    "先前的疗愈案例：长期高压力用户对慢速、暖色调的森林场景响应最佳。",
    "视觉生成时，建议加入缓慢的云雾流动或水面波纹，以触发自主性注意恢复。"
]

def build_vectorstore():
    """构建或加载向量数据库"""
    persist_dir = "./chroma_db"
    if os.path.exists(persist_dir):
        # 如果已存在则直接加载
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embedding_model)
    else:
        # 否则新建
        docs = [{"page_content": text} for text in DEFAULT_KNOWLEDGE]
        from langchain_core.documents import Document
        documents = [Document(page_content=text) for text in DEFAULT_KNOWLEDGE]
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        split_docs = text_splitter.split_documents(documents)
        vectorstore = Chroma.from_documents(split_docs, embedding_model, persist_directory=persist_dir)
        vectorstore.persist()
    return vectorstore

def get_retriever():
    vectorstore = build_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": 3})