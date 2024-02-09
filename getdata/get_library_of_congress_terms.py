
import requests
import csv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text 

# Load environment variables and set up credentials
load_dotenv()
key_vault_uri = os.getenv("KEY_VAULT_URI")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)
library_file = './data/library_of_congress_parsed.csv'

# Retrieve secrets
gpt_key = secret_client.get_secret("gpt4-api-key").value
chat_model = "gpt-4-1106-preview"
server_name = secret_client.get_secret("azuresql-db-icpsrserver").value
database_name = secret_client.get_secret("icpsr-database").value
username = secret_client.get_secret("sql-adminusername").value
password = secret_client.get_secret("sql-adminpassword").value

# Construct the connection URL and create engine
connection_url = f"mssql+pyodbc://{username}:{password}@{server_name}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(connection_url, connect_args={"timeout": 30})


def create_url_library_of_congress(URI):
    
    file_type = '.json'
    base_url = 'https://id.loc.gov'
    #print(URI)
    url = base_url.strip()+URI[0].strip()+file_type.strip()  
    #print(url)
    return url


def generate_api_content_library_of_congress(url):
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        for item in data:
            if "@type" in item and "http://www.loc.gov/mads/rdf/v1#TopicElement" in item["@type"]:
                if "http://www.loc.gov/mads/rdf/v1#elementValue" in item:
                    value = item["http://www.loc.gov/mads/rdf/v1#elementValue"][0]["@value"]
                    if value is not None:
                        insert_statement = text("INSERT INTO dbo.loc_keywords (keyword) VALUES (:value)")
                        with engine.connect() as connection:
                            transaction = connection.begin()
                            try:
                                result = connection.execute(insert_statement, {"value": value})
                                transaction.commit()  # Explicitly commit the transaction
                                if result.rowcount > 0:
                                    print(f"Record inserted successfully. Value: {value}. Rows affected: {result.rowcount}")
                                else:
                                    print("No records were inserted.")
                            except Exception as e:
                                transaction.rollback()  # Roll back the transaction in case of error
                                print(f"An error occurred during insertion: {e}")
                                # Removed return statement from here to allow processing of all items

                                    
def main():
    
    with open(library_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            generate_api_content_library_of_congress(create_url_library_of_congress(row))

                  

if __name__ == "__main__":
    main()
