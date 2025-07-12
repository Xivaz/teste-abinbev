from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow.models import Variable
from airflow.providers.azure.hooks.wasb import WasbHook
from airflow.providers.microsoft.azure_blob_containers.transfers.wasb_to_azure_blob import WasbToAzureBlobOperator
# DAG definition
# Esta DAG faz ingestão de dados brutos da API do https://api.openbrewerydb.org para o Azure Blob Storage 
# e depois efetua a transformação desses dados para o Databricks Delta Lake
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
dir_raw_data = '/openbrewrydb/raw/%Y/%m/%d/raw_data.json'
dag = DAG(      
    'ingest_raw_data',
    default_args=default_args,
    description='Faz o Ingest raw data da origem openberwerydb para o Azure Blob Storage',
    schedule_interval='@daily',
    catchup=False,
)
# Tarefa para fazer a leitura da api do openbrewerydb e gerar a camada raw 
def ingest_raw_data():
    import requests
    import json
    from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
    # URL da API
    url = 'https://api.openbrewerydb.org/v1/breweries'
    # Fazendo a requisição GET
    response = requests.get(url)
    # Verifica se a requisição foi bem-sucedida
    if response.status_code == 200:
        data = response.json()
        # Salva os dados em um arquivo JSON
        with open(dir_raw_data, 'w') as f:
            json.dump(data, f)
    else:
        raise Exception(f"Failed to fetch
         data: {response.status_code}")  

# Definindo a tarefa de ingestão de dados  
# Tarefa para fazer a leitura da api do openbrewerydb e gerar a camada raw
wasb_hook = WasbHook(wasb_conn_id='azure_blob_storage')
container_name = Variable.get("azure_blob_container")
blob_name = Variable.get("raw_data_blob_name")
    
# Example: Download the blob to a local file
# wasb_hook.get_file(container_name=container_name, blob_name=blob_name, filename=dir_raw_data)

# Tarefa Início
inicio = DummyOperator(
    task_id='start',
    dag=dag,
)

# Tarefa ingestão de dados RAW
ingest_raw_data = PythonOperator(
    task_id='ingest_raw_data',      
    python_callable=ingest_raw_data,
    dag=dag,
)

# Tarefa de upload para o Azure Blob Storage
upload_to_azure_blob = WasbToAzureBlobOperator(
    task_id='upload_to_azure_blob',
    wasb_conn_id='azure_blob_storage',
    container_name=Variable.get("azure_blob_container"),
    blob_name=Variable.get("raw_data_blob_name"),
    file_path=dir_raw_data,
    dag=dag,
)

# Tarefa Fim
fim = DummyOperator(        
    task_id='end',
    dag=dag,
)

# Definindo a ordem das tarefas
inicio >> ingest_raw_data >> upload_to_azure_blob >> fim
