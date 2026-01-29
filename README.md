# Agent Ingestion Executor

## Overview

The Agent Ingestion Executor is a powerful tool designed for interacting with various datasets. It allows users to easily ingest, query, and manipulate data through a streamlined interface.

## Configuration Builder

Before using the Agent Ingestion Executor, it's essential to set up the configuration builder. This component allows you to define the parameters and specifications for the datasets you intend to work with.

1. **Load the Specification Builder**: 
   Use the following command to start the Streamlit app for the specification builder:

   ```bash
   python3 -m streamlit run app_api_specification_builder/streamlit_app.py
   ```

   This app helps you create and manage dataset specifications.

2. **Load the Ingestion Executor**: 
   Start the main ingestion executor Streamlit app with:

   ```bash
   python3 -m streamlit run agent_ingestion_executor/executor_streamlit_app.py
   ```

   This app provides an interface to authenticate, query, and interact with datasets.

## Features

- **User Authentication**: Secure access to different datasets based on user permissions.
- **Flexible Queries**: Users can perform complex queries and obtain summarized insights.
- **Data Display**: Easily view and download results in DataFrame format.
- **Extensible**: Capable of integrating additional tools and functionalities.

## Usage

1. **Start the Applications**:
   - Begin with the configuration builder to set dataset parameters.
   - Then, run the ingestion executor to interact with your datasets.

2. **Authenticate**: 
   Provide your username to access the system.

3. **Interact with Datasets**:
   - Specify the dataset you wish to query.
   - Use the input box to enter ingestion commands or queries.
   - Results will be displayed in an interactive manner.

