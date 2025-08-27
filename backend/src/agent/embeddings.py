import logging
from typing import Any, Dict, List, Optional

from langchain_core.embeddings import Embeddings
from pinecone import Pinecone as PineconeClient
from pinecone import (
    PineconeAsyncio as PineconeAsyncioClient
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SecretStr,
    model_validator
)
import os
from dotenv import load_dotenv
from typing_extensions import Self

load_dotenv()

logger = logging.getLogger(__name__) #Logging API 

DEFAULT_BATCH_SIZE = 64

class PineconeEmbeddings(BaseModel):
    #Defining expected params when using this class
    client: PineconeClient = PrivateAttr(default=None)
    async_client: Optional[PineconeAsyncioClient] = PrivateAttr(default=None)
    model: str
    batch_size: Optional[int] = None
    query_params: Dict = Field(default_factory=dict)
    document_params: Dict = Field(default_factory=dict)

    dimension: Optional[int] = None

    pinecone_api_key: SecretStr = Field(
        default_factory=os.getenv("PINECONE_API_KEY", error_message = "Pinecone API key not found"),
    )

    #ConfigDict is a data structure for 
    model_config = ConfigDict(
        extra="forbid", #forbid other params, that user adds
        populate_by_name=True,
        protected_namespaces=(),
    )

    #Load Pinecone async
    @property
    def async_client(self) -> PineconeAsyncioClient:
        return PineconeAsyncioClient(
            api_key = self.pinecone_api_key.get_secret_value(), source_tag = "langchain"
        )
    
    @model_validator(mode="before")
    @classmethod
    def set_default_config(cls, values: dict) -> Any:
        default_config_map = {
            "multilingual-e5-large": {
                "batch_size": 96,
                "query_params": {"input_type": "query", "truncate": "END"},
                "document_params": {"input_type": "passage", "truncate": "END"},
                "dimension": 384,
            }            
        }

        model = values.get("model")
        if model in default_config_map:
            config = default_config_map[model]
            for key, value in config.items():
                if key not in values:
                    values[key] = value
        return values

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        api_key_str = self.pinecone_api_key.get_secret_value()
        client = PineconeClient(api_key=api_key_str, source_tag = "langchain")
        self._client = client
    
    #Defining the batches (dávky)
    def get_batch_iterator(self, text: List[str]):
        if self.batch_size is None:
            batch_size = DEFAULT_BATCH_SIZE
        else:
            batch_size = self.batch_size
        
    #It just iterates through the uploaded text, wait for the model to return floats (transformed strings) and adding to embeddings (list of lists of floats)
    def embed_documents(self, texts: List[str]):
        embeddings: List[List[float]] = []

        iter, batch_size = self.get_batch_iterator(texts)
        for i in iter:
            response = self.embed_text(
                model = self.model,
                parameters = self.document_params,
                texts=texts[i : i  + batch_size],
            )

            embeddings.extend(r["values"] for r in response)
        return embeddings
    
    #Takes the user query and awaits for embedding, which is the first in the response (hence index 0)
    """ Expected output
    {
        'data': [{'values': [0.1, 0.2, ...]}, ...],
        'model': 'model-name',
        'usage': {'total_tokens': 6}
    } """

    async def embed_query(self, text: str) -> List[float]:
        embeddings = await self.embed_text(
            model = self.model,
            parameters = self.query_params,
            texts = [text]
        )
        return embeddings[0]("values")
    

    async def embed_text(self, texts: List[str], model: str, parameters: dict):
        async with self.async_client as client:
            embeddings = await client.inference.embed(
                model = model,
                inputs = texts,
                parameters = parameters
            )

        return embeddings

    #Standard embedding = returns a list of floats and is good for semantic search, recommendations, clustering. Tries to capture the meaning
    #Sparse embeddings = returns a list of 0 and 1 and is used for exact keyword matching (for critical docs like legal or medication)