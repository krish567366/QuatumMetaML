import os
import re
import hashlib
import requests
import pandas as pd
import numpy as np
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Union, Generator
from pydantic import BaseModel, ValidationError, validator
from sqlalchemy import create_engine
import snowflake.connector
from google.cloud import bigquery
import boto3
from datasets import load_dataset as hf_load
import dask.dataframe as dd
from kaggle.api.kaggle_api_extended import KaggleApi
from .license import LicenseValidator
from .config import CommercialConfig

class DataSourceType(str, Enum):
    HUGGINGFACE = "huggingface"
    CSV = "csv"
    EXCEL = "excel"
    PARQUET = "parquet"
    SQL = "sql"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    S3 = "s3"
    HTTP = "http"
    KAGGLE = "kaggle"
    DASK = "dask"
    GENERATOR = "generator"

class DataSourceConfig(BaseModel):
    """Configuration model for data loading"""
    source_type: DataSourceType
    parameters: Dict[str, Any]
    cache: bool = True
    streaming: bool = False
    chunk_size: int = 10_000

    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v <= 0:
            raise ValueError("Chunk size must be positive")
        return v

class EnterpriseDataFetcher:
    def __init__(self, config: CommercialConfig):
        self.config = config
        self.license = LicenseValidator(config.license_key)
        self._cache_dir = Path(os.getenv("DATA_CACHE_DIR", "/data_cache"))
        self._create_cache()
        
        # Initialize clients
        self._s3 = boto3.client('s3') if self._check_license("s3") else None
        self._bq = bigquery.Client() if self._check_license("bigquery") else None
        self._kaggle = KaggleApi() if self._check_license("kaggle") else None

    def _create_cache(self):
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _check_license(self, feature: str) -> bool:
        """Check license for a specific data source"""
        return self.license.validate(f"data_{feature}")

    def load(self, config: DataSourceConfig) -> Union[pd.DataFrame, dd.DataFrame, Generator]:
        """Main entry point for loading data"""
        try:
            validated_config = DataSourceConfig(**config.dict())
        except ValidationError as e:
            raise ValueError(f"Invalid data config: {e}")

        if not self._check_license(validated_config.source_type.value):
            raise PermissionError(f"License required for {validated_config.source_type} data source")

        loader = self._get_loader(validated_config.source_type)
        
        if validated_config.streaming:
            return self._stream_data(loader, validated_config)
            
        return loader(validated_config.parameters)

    def _get_loader(self, source_type: DataSourceType):
        """Get the appropriate loader function"""
        return {
            DataSourceType.HUGGINGFACE: self._load_huggingface,
            DataSourceType.CSV: self._load_file,
            DataSourceType.EXCEL: self._load_file,
            DataSourceType.PARQUET: self._load_file,
            DataSourceType.SQL: self._load_sql,
            DataSourceType.SNOWFLAKE: self._load_snowflake,
            DataSourceType.BIGQUERY: self._load_bigquery,
            DataSourceType.S3: self._load_s3,
            DataSourceType.HTTP: self._load_http,
            DataSourceType.KAGGLE: self._load_kaggle,
            DataSourceType.DASK: self._load_dask,
            DataSourceType.GENERATOR: self._load_generator,
        }[source_type]

    def _load_huggingface(self, params: Dict) -> pd.DataFrame:
        """Load dataset from Hugging Face Hub"""
        return hf_load(
            params["dataset_name"],
            cache_dir=str(self._cache_dir / "huggingface"),
            **params.get("kwargs", {})
        ).to_pandas()

    def _load_file(self, params: Dict) -> pd.DataFrame:
        """Load local files (CSV, Excel, Parquet)"""
        path = Path(params["path"])
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found")

        if params["source_type"] == DataSourceType.CSV:
            return pd.read_csv(path, **params.get("read_kwargs", {}))
        elif params["source_type"] == DataSourceType.EXCEL:
            return pd.read_excel(path, **params.get("read_kwargs", {}))
        elif params["source_type"] == DataSourceType.PARQUET:
            return pd.read_parquet(path, **params.get("read_kwargs", {}))

    def _load_sql(self, params: Dict) -> pd.DataFrame:
        """Load data from SQL database"""
        engine = create_engine(params["connection_string"])
        return pd.read_sql(
            params["query"],
            engine,
            chunksize=params.get("chunk_size")
        )

    def _load_snowflake(self, params: Dict) -> pd.DataFrame:
        """Load data from Snowflake data warehouse"""
        conn = snowflake.connector.connect(
            user=params["user"],
            password=params["password"],
            account=params["account"],
            warehouse=params["warehouse"],
            database=params["database"],
            schema=params["schema"]
        )
        return pd.read_sql(params["query"], conn)

    def _load_bigquery(self, params: Dict) -> pd.DataFrame:
        """Load data from Google BigQuery"""
        query = f"""
            SELECT * 
            FROM `{params['project']}.{params['dataset']}.{params['table']}`
            {params.get('where_clause', '')}
        """
        return self._bq.query(query).to_dataframe()

    def _load_s3(self, params: Dict) -> pd.DataFrame:
        """Load data from S3 bucket"""
        obj = self._s3.get_object(
            Bucket=params["bucket"],
            Key=params["key"]
        )
        return pd.read_parquet(obj['Body'])

    def _load_http(self, params: Dict) -> pd.DataFrame:
        """Load data from HTTP/HTTPS endpoint"""
        cache_key = hashlib.md5(params["url"].encode()).hexdigest()
        cache_path = self._cache_dir / "http" / f"{cache_key}.parquet"

        if cache_path.exists():
            return pd.read_parquet(cache_path)

        df = pd.read_csv(params["url"])
        if params.get("cache", True):
            df.to_parquet(cache_path)
        return df

    def _load_kaggle(self, params: Dict) -> pd.DataFrame:
        """Load dataset from Kaggle"""
        self._kaggle.authenticate()
        self._kaggle.dataset_download_files(
            params["dataset"],
            path=str(self._cache_dir / "kaggle"),
            unzip=True
        )
        return pd.read_csv(next((self._cache_dir / "kaggle").glob("*.csv")))

    def _load_dask(self, params: Dict) -> dd.DataFrame:
        """Load large dataset using Dask"""
        return dd.read_parquet(
            params["path_pattern"],
            engine="pyarrow",
            **params.get("read_kwargs", {})
        )

    def _load_generator(self, params: Dict) -> pd.DataFrame:
        """Generate synthetic data"""
        data_type = params.get("type", "linear")
        n_samples = params.get("samples", 1000)
        n_features = params.get("features", 10)

        if data_type == "linear":
            X = np.random.randn(n_samples, n_features)
            y = X.dot(np.random.randn(n_features)) + np.random.normal(0, 0.1, n_samples)
            return pd.DataFrame(X, columns=[f"x_{i}" for i in range(n_features)]).assign(y=y)
        elif data_type == "classification":
            # More complex synthetic data
            pass
        else:
            raise ValueError(f"Unknown generator type: {data_type}")

    def _stream_data(self, loader, config: DataSourceConfig) -> Generator:
        """Stream large datasets in chunks"""
        if config.source_type == DataSourceType.S3:
            return self._stream_s3(config.parameters, config.chunk_size)
        elif config.source_type == DataSourceType.SQL:
            return self._stream_sql(config.parameters, config.chunk_size)
        else:
            raise NotImplementedError(f"Streaming not supported for {config.source_type}")

    def _stream_s3(self, params: Dict, chunk_size: int) -> Generator:
        """Stream large files from S3"""
        paginator = self._s3.get_paginator('select_object_content')
        result = paginator.paginate(
            Bucket=params["bucket"],
            Key=params["key"],
            ExpressionType='SQL',
            Expression=f"SELECT * FROM S3Object LIMIT {chunk_size}",
            InputSerialization={'Parquet': {}},
            OutputSerialization={'CSV': {}}
        )
        for page in result:
            yield pd.read_csv(page['Payload'])

    def _stream_sql(self, params: Dict, chunk_size: int) -> Generator:
        """Stream data from SQL databases"""
        engine = create_engine(params["connection_string"])
        with engine.connect().execution_options(stream_results=True) as conn:
            result = conn.exec_driver_sql(params["query"])
            while True:
                chunk = result.fetchmany(chunk_size)
                if not chunk:
                    break
                yield pd.DataFrame(chunk, columns=result.keys())

    def supported_sources(self) -> list:
        """Get list of supported data sources"""
        return [source.value for source in DataSourceType]

    def clear_cache(self):
        """Clear all cached data"""
        for path in self._cache_dir.glob("**/*"):
            if path.is_file():
                path.unlink()