import pandas as pd
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
import requests
import os

# Load environment variables and set up credentials
load_dotenv()
key_vault_uri = os.getenv("KEY_VAULT_URI")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

# Retrieve secrets
gpt_key = secret_client.get_secret("gpt4-api-key").value
chat_model = "gpt-4"
base_url = "https://api.umgpt.umich.edu/azure-openai-api" #secret_client.get_secret("openai-api-base").value
shortcode = secret_client.get_secret("shortcode").value
headers = {
    "Authorization": f"Bearer {gpt_key}"
}
#Files
input_file = './gpt_sample.csv'
output_file = './gpt_sample_processed.csv'


# Create Azure client
client = AzureOpenAI(
    api_key=gpt_key,
    api_version=chat_model, 
    azure_endpoint=base_url,
    organization=shortcode#,
    #headers = headers
)

# Temperature for GPT-4 responses
TEMPERATURE = .5

# Define function to interact with ChatGPT
def chatgpt(prompt, TEMPERATURE):
    response = client.chat.completions.create(
        model=chat_model, messages=[{"role": "user", "content": prompt}], seed=1, temperature=TEMPERATURE
    )
    responses = response.choices[0].message.content.strip()
    gpt_list = [item.strip() for item in responses.split(",")]
    return gpt_list

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
        gpt_response = chatgpt(text, TEMPERATURE)
        
        # Append the results to the output DataFrame
        output_df = output_df.append({'study_id': study_id, 'text': text, 'gpt_response': gpt_response}, ignore_index=True)
    
    # Write the output DataFrame to a CSV file
    output_df.to_csv(output_file, index=False)

# Main function to kickstart the process
if __name__ == "__main__":
    input_csv = input_file  # Path to your input CSV file
    output_csv = output_file  # Path to your desired output CSV file
    process_csv(input_csv, output_csv)
