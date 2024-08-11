from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

modelPath = "BAAI/bge-small-en-v1.5" 
model_kwargs = {'device':'cpu','trust_remote_code':'True'}
encode_kwargs = {'normalize_embeddings': True}

# Initialize an instance of HuggingFaceEmbeddings with the specified parameters
embeddings = HuggingFaceEmbeddings(
    model_name=modelPath,     # Provide the pre-trained model's path
    model_kwargs=model_kwargs, # Pass the model configuration options
    encode_kwargs=encode_kwargs # Pass the encoding options
)

chroma = chromadb.PersistentClient(path="./chroma_db")


from chromadb.api import AdminAPI, ClientAPI
def collection_exists(client:ClientAPI, collection_name):
    print(collection_name)
    collections = client.list_collections()
    print(collections)
    filtered_collection = filter(lambda collection: collection.name == collection_name, collections)
    found = any(filtered_collection)
    return found


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

def load_slack_communication_guidelines(chroma, embeddings):
    collection_name = "langchain_tools"
    urls = [
        "https://slack.com/blog/collaboration/etiquette-tips-in-slack",
        "https://www.forbes.com/sites/theyec/2021/02/17/working-remotely-eight-tips-to-communicate-professionally-and-effectively-on-slack/",
        "https://www.joinglyph.com/blog/slack-etiquette-dos-and-donts",
        "https://www.m.io/blog/slack-etiquette",
        "https://clickup.com/blog/slack-etiquette/",
        "https://www.harmonizehq.com/blog/slack-etiquette-guide/",
        "https://topresume.com/career-advice/slack-etiquette-at-work",
        "https://www.talaera.com/blog/slack-communication/"
    ]
    
    if not collection_exists(chroma, collection_name):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection(collection_name)
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=emb,
                metadatas=doc.metadata,
                documents=[doc.page_content]
            )

# load_slack_communication_guidelines(chroma, embeddings)

slack_communication_guidelines = create_retriever_tool(
    Chroma(client=chroma, collection_name="slack_communication_guidelines", embedding_function=embeddings).as_retriever(),
    "slack_communication_guidelines",
    "Search for guidelines on appropriate channels, tone, and format for Slack communications within the organization. Use this tool for any questions about Slack communication etiquette and best practices."
)


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid
from typing import List

urls: List[str] = [
    "https://www.linkedin.com/advice/3/heres-how-you-can-tailor-your-communication-q2yhf",
    "https://leaddev.com/personal-development/navigating-different-communication-styles-engineers",
    "https://www.forbes.com/sites/forbesagencycouncil/2022/08/02/creating-a-content-strategy-that-speaks-to-the-c-suite/",
    "https://asana.com/resources/what-is-program-management",
    "https://www.ccl.org/leadership-programs/leadership-at-the-peak-training-for-senior-executives/",
    "https://clockwise.software/blog/what-is-the-c-suite/",
    "https://contently.com/2023/11/08/a-guide-to-crafting-the-perfect-content-format/"
]

def load_audience_specific_examples(chroma, embeddings):
    if not collection_exists(chroma, "audience_specific_examples"):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection("audience_specific_examples")
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                metadata = doc.metadata.copy()
                metadata['source'] = metadata.get('source', '')
                collection.add(
                    ids=[str(uuid.uuid1())],
                    embeddings=emb,
                    metadatas=[metadata],
                    documents=[doc.page_content]
                )
        except Exception as e:
            print(f"Error loading documents: {e}")

# load_audience_specific_examples(chroma, embeddings)

audience_specific_examples = create_retriever_tool(
    Chroma(
        client=chroma,
        collection_name="audience_specific_examples",
        embedding_function=embeddings
    ).as_retriever(),
    "audience_specific_examples",
    "Search for examples of communication styles and content strategies for Program Managers, Engineers, and C-suite executives. Use this tool to understand the expected format, tone, and content for each audience group."
)


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores import Chroma
import chromadb
import uuid

urls = [
    "https://www.aha.io/roadmapping/guide/launch/how-to-write-excellent-release-notes",
    "https://www.launchnotes.com/blog/how-to-write-great-product-release-notes-the-ultimate-guide",
    "https://www.productlogz.com/blog/how-to-write-release-notes",
    "https://www.appcues.com/blog/release-notes-examples",
    "https://www.released.so/articles/the-ultimate-guide-to-writing-effective-release-notes-templates-and-examples",
    "https://www.outverse.com/guides/how-to-write-software-release-notes-template-examples",
    "https://www.techwriterdiary.com/l/release-notes-basic-principles/",
    "https://www.onset.io/blog/release-notes-best-practices"
]

def load_release_notes_best_practices(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection("langchain_tools")
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
                )
        except Exception as e:
            print(f"Error loading release notes best practices: {e}")

# load_release_notes_best_practices(chroma, embeddings)

release_notes_best_practices = Chroma(
    client=chroma,
    collection_name="internal_review_guidelines",
    embedding_function=embeddings,
).as_retriever()

release_notes_best_practices_tool = create_retriever_tool(
    release_notes_best_practices,
    "release_notes_best_practices",
    "Search for best practices in writing effective release notes. For any questions about release notes principles and guidelines, you must use this tool!"
)


import uuid
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool

urls = [
    "https://bizfluent.com/how-10002395-conduct-organizational-review.html",
    "https://www.powerdms.com/policy-learning-center/why-it-is-important-to-review-policies-and-procedures",
    "https://www.launchnotes.com/blog/the-ultimate-guide-to-internal-feedback-in-the-workplace",
    "https://chisellabs.com/blog/internal-feedback/",
    "https://www.ecgi.global/sites/default/files/codes/documents/kpmg_internal_control_practical_guide.pdf",
    "https://ero.govt.nz/our-research/effective-internal-evaluation-for-improvement",
    "https://www.utrgv.edu/curriculum-assessment/_files/022024/apr-process.pdf"
]

def load_internal_review_guidelines(chroma, embeddings, collection_name="internal_review_guidelines"):
    if not collection_exists(chroma, collection_name):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection(collection_name)
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
                )
            print(f"Successfully loaded documents into {collection_name} collection.")
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False
    else:
        print(f"Collection {collection_name} already exists. Skipping document loading.")
    return True

# load_internal_review_guidelines(chroma, embeddings):

chroma_retriever = Chroma(
    client=chroma,
    collection_name="internal_review_guidelines",
    embedding_function=embeddings,
).as_retriever()

internal_review_guidelines = create_retriever_tool(
    chroma_retriever,
    "internal_review_guidelines",
    "Search for information about organizational review procedures and feedback incorporation methods. Use this tool for any questions related to internal review guidelines, feedback processes, or evaluation procedures."
)

from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
import uuid

urls = [
    "https://www.bp-3.com/blog/process-management-architecture-overview-of-methods-features-and-capabilities",
    "https://www.processmaker.com/blog/process-optimization-explained/",
    "https://www.redhat.com/architect/architecture-documentation-practices",
    "https://www.workingsoftware.dev/software-architecture-documentation-the-ultimate-guide/",
    "https://enterprise-architecture-template.com/",
    "https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/tech-forward/crafting-the-optimal-model-for-the-it-architecture-organization",
    "https://www.axelos.com/resource-hub/practice/architecture-management-itil-4-practice-guide",
    "https://www.valueblue.com/blog/2021/10/enterprise-architecture-and-business-process-management-a-match-made-in-heaven-for-current-state-insights",
    "https://orgmapper.com/what-is-organizational-mapping-understand-this-business-architecture-concept/"
]

def load_system_architecture_docs(chroma_client, embeddings):
    collection_name = "system_architecture_search"
    if not collection_exists(chroma_client, collection_name):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma_client.create_collection(collection_name)
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

# load_system_architecture_docs(chroma, embeddings)

system_architecture_vectorstore = Chroma(
    client=chroma,
    collection_name="system_architecture_search",
    embedding_function=embeddings,
)

system_architecture_docs = create_retriever_tool(
    system_architecture_vectorstore.as_retriever(),
    "system_architecture_search",
    "Search for information about system architecture, process management, and optimization. Use this tool for questions related to organizational system architecture and effective process management."
)
