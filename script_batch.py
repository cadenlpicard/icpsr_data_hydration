
from openai import AzureOpenAI
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
import io
import csv


# Set GLOBAL 
result_size = 10
TEMPERATURE = .5
STUDYID = 0

# Initialize results and missing variables
icpsr_result, elsst_result, loc_result = "", "", ""
elsst_missing, gpt_missing, loc_result = "", "", ""

# Initialize check flags
check_icpsr, check_elsst, check_loc = False, False, False

# Load environment variables and set up credentials
load_dotenv()
key_vault_uri = os.getenv("KEY_VAULT_URI")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)


# Azure SQL - Retrieve secrets
server_name = secret_client.get_secret("azuresql-db-icpsrserver").value
database_name = secret_client.get_secret("icpsr-database").value
username = secret_client.get_secret("sql-adminusername").value
password = secret_client.get_secret("sql-adminpassword").value

# Construct the connection URL and create engine
connection_url = f"mssql+pyodbc://{username}:{password}@{server_name}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(connection_url, connect_args={"timeout": 30})
# Create an in-memory stream to hold the CSV data
proxy = io.StringIO()
writer = csv.writer(proxy)


# GPT - Retrieve secrets
gpt_key = secret_client.get_secret("gpt4-api-key").value
shortcode = secret_client.get_secret("shortcode").value
base_url = secret_client.get_secret("openai-api-base").value
chat_model = "2023-05-15" 
deploy_id = 'gpt-4-turbo' 

#Create OpenAI client
client = AzureOpenAI(
    api_key=gpt_key,  
    api_version=chat_model,
    azure_endpoint = base_url,
    organization = shortcode
)


# Define function to interact with ChatGPT
def chatgpt(prompt,TEMPERATURE):   
    response = client.chat.completions.create(
    model=deploy_id, messages=[{"role": "user", "content": prompt}], seed=1, temperature = TEMPERATURE
    )
    
    responses = response.choices[0].message.content.strip()
    gpt_list = [item.strip() for item in responses.split(",")]
    return gpt_list



#Files
input_file = './gpt_sample.csv'
output_file = './gpt_sample_processed.csv'

def get_gpt_list(text_to_analyze):

    passage_prompt = f"""
              Here is a passage of text: {text_to_analyze}.As an expert in social science subject terms, analyze the passage to understand the main context and themes. Limit the results to the {result_size} best of the most relevant phrases. Return them
              in a comma delimited list. The themes and context descriptions should be no more than 3 words long and should not have special characters.
              Do not provide any additional commentary or feedback.
              """
    gpt_words = chatgpt(passage_prompt,TEMPERATURE)
    return [word.lower() for word in gpt_words[:10]]

def get_dictionary_terms(file_name, gpt_list, size):
    file_keywords = return_keyword_list(file_name)[:20000]
    file_list = ",".join(word.lower().strip() for word in file_keywords)

    list_compare_prompt = f"""I am going to give you two lists. The first list is called "GPT list" and the second list is called "Subject Terms List".
                        Based on the words in the "GPT list", find phrases in the "Subject Terms List" that describe similar contexts and themes. 
                        The result set should be comma delimited list without numbering.
                        This is the GPT list:{gpt_list}
                        This is the subject terms list: {file_list}
                        Order the list alphabetically from A-Z.
                        As an expert in social science subject terms, limit the results to the {result_size} best of the most relevant phrases sourced from the "Subject Terms List"
                        Do not provide any additional commentary or feedback.
                        """
    return chatgpt(list_compare_prompt,TEMPERATURE)


# Define function to find missing keywords
def missing_keywords(keyword_list, icpsr_keywords):
    matches = []  
    for item in keyword_list:
        if item.strip() not in icpsr_keywords:
            matches.append(item.strip())  
    return ",".join(matches)  

# Function to process CSV file and output results
def process_csv(input_file, output_file):
    # Read the input CSV file
    df = pd.read_csv(input_file)
    
    # Prepare the output DataFrame
    output_df = pd.DataFrame(columns=['study_id', 'text', 'gpt_response'])
    
    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        study_id = row['STUDY']
        text = row['DATA']
        
        # Generate GPT response
        gpt_response = get_gpt_list(text)
        icpsr_keywords = return_keyword_list("2")    
        gpt_missing = missing_keywords(gpt_response, icpsr_keywords)
        icpsr_result = get_dictionary_terms("2", gpt_response, result_size)
        
        #print(gpt_response)
        
        # Append the results to the output DataFrame
        output_df = output_df.append({'study_id': study_id, 'text': text, 'gpt_response': gpt_response,'icpr_keywords':icpsr_result, 'missing_icpsr': gpt_missing }, ignore_index=True)
        #print(output_df)
    
    # Write the output DataFrame to a CSV file
    output_df.to_csv(output_file, index=False)
    
# Define function to retrieve keyword list
def return_keyword_list(db_id, header_name="keyword"):
    sql_query = text(
        "exec dbo.return_keywords :db_id"
    )
    with engine.connect() as connection:
        result = connection.execute(sql_query, {"db_id": db_id})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return [word.lower() for word in df[header_name].tolist()]

# Main function to kickstart the process
if __name__ == "__main__":
    input_csv = input_file  # Path to your input CSV file
    output_csv = output_file  # Path to your desired output CSV file
    
    process_csv(input_csv, output_csv)
