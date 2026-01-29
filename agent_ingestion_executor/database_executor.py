from google.cloud import bigquery
import os
import pandas as pd
import json

from langchain_core.tools import tool 
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

import sqlite3

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_big_query_service_key.json"

@tool 
def ingest_and_query_database(params, filters=None):
    """    
    This function queries the database based on the provided parameters. It allows optional filtering of results.
    This function ingests the data into memory and offers a sample of 30 example rows.

    Args:
        params (dict): A dictionary containing the dataset name and columns to fetch.
                        Expected keys are "dataset" (str) and "columns" (list of str).
        filters (dict, optional): A dictionary specifying filters to apply on the query.
                                  Format should be {"column_name": value}. Defaults to None.

    Example:
        params = {
            "dataset": "new_york_311.311_service_requests",
            "columns": ["unique_key", "created_date", "agency_name"]
        }
        filters={"agency_name": "'NYPD'"}
    """
    print(params)
    print(filters)

    client = bigquery.Client()

    dataset = params["dataset"]
    columns = ", ".join(params["columns"])
    
    query = f"""
    SELECT
        {columns}
    FROM `bigquery-public-data.{dataset}`
    {f"WHERE {' AND '.join(f'{k} = {v}' for k, v in filters.items())}" if filters else ''}
    LIMIT 10000
    """

    df = client.query(query).to_dataframe()

    if df.empty:
        return []

    os.makedirs("local_db", exist_ok=True)
    db_path = f"local_db/{params['dataset'].replace('.', '_')}.db"

    table_name = dataset.replace(".", "_")

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    sample_size = min(30, len(df))
    sampled_df = df.sample(n=sample_size, random_state=None)

    conn.close()

    return sampled_df.to_json(orient='records', date_format='iso')

model = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.1,
    max_tokens=4000,
    timeout=70
)

database_executor_agent = create_agent(
    model=model,
    tools=[ingest_and_query_database],
)

def load_dataset_specs(path="data/api_data_specifications.json"):
    with open(path, "r") as f:
        return json.load(f)

def build_vector_store(specs):
    docs = []
    for spec in specs:
        text = f"""
        Dataset: {spec['dataset']}
        Columns: {', '.join(spec['columns'])}
        """
        docs.append(
            Document(
                page_content=text,
                metadata=spec
            )
        )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.from_documents(docs, embeddings)

def retrieve_relevant_spec(user_request, vector_store):
    results = vector_store.similarity_search(user_request, k=1)
    return results[0].metadata

def build_agent_prompt(user_request, dataset_spec):
    dataset = dataset_spec["dataset"]
    columns = ", ".join(dataset_spec["columns"])

    return f"""
You are an assistant that uses tools to initiate the ingestion of specified databases. 
The tools only return a small sample portion of the ingested data.

User request:
{user_request}

Available database:
- Dataset: {dataset}
- Columns: {columns}

1. Use ONLY the dataset and columns above when answering.
2. Focus on very brief summaries, insights, or aggregations; do NOT display large data samples.
"""

def database_agent_entrypoint(inputs, username):
    messages = inputs["messages"]
    user_request = messages[-1].content

    specs = load_dataset_specs()
    vector_store = build_vector_store(specs)

    selected_spec = retrieve_relevant_spec(user_request, vector_store)

    print(selected_spec)
    # Check if the user is allowed to access the dataset
    allowed_users = selected_spec["permissions"]["allowed_users"]
    if username not in allowed_users:
        return {"messages": [AIMessage(content="User not authorized to access this dataset.")]} 

    agent_prompt = build_agent_prompt(user_request, selected_spec)

    response = database_executor_agent.invoke(
        {"messages": [HumanMessage(content=agent_prompt)]}
    )

    return response

def run_database_agent(user_request: str, username: str):
    history = [HumanMessage(content=user_request)]
    return database_agent_entrypoint({"messages": history}, username)

