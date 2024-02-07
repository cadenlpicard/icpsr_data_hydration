import openai
import pandas as pd
from flask import Flask, request, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

# Initialize Flask app
app = Flask(__name__)

# Set result size
result_size = 10

# Initialize results and missing variables
icpsr_result, elsst_result, mesh_result = "", "", ""
elsst_missing, gpt_missing, mesh_missing = "", "", ""

# Initialize check flags
check_icpsr, check_elsst, check_mesh = False, False, False

# Load environment variables and set up credentials
load_dotenv()
key_vault_uri = os.getenv("KEY_VAULT_URI")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

# Retrieve secrets
gpt_key = secret_client.get_secret("gpt4-api-key").value
chat_model = "gpt-4-1106-preview"
server_name = secret_client.get_secret("azuresql-db-icpsrserver").value
database_name = secret_client.get_secret("icpsr-database").value
username = secret_client.get_secret("sql-adminusername").value
password = secret_client.get_secret("sql-adminpassword").value

# Construct the connection URL and create engine
connection_url = f"mssql+pyodbc://{username}:{password}@{server_name}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
print(connection_url)
engine = create_engine(connection_url, connect_args={"timeout": 30})

# Define function to interact with ChatGPT
def chatgpt(gpt_key, chat_model, prompt):
    openai.api_key = gpt_key
    response = openai.chat.completions.create(
        model=chat_model, messages=[{"role": "user", "content": prompt}], seed=1, temperature = .5
    )
    responses = response.choices[0].message.content.strip()
    gpt_list = list(responses.split(","))
    return gpt_list


# Define function to retrieve keyword list
def return_keyword_list(db_id, header_name="keyword"):
    sql_query = text(
        "SELECT keyword FROM icpsr_meta.dbo.keywords WHERE source_db_id = :db_id"
    )
    with engine.connect() as connection:
        result = connection.execute(sql_query, {"db_id": db_id})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return [word.lower() for word in df[header_name].tolist()]


######################################################
################# Look at dictionaries################
######################################################


def get_dictionary_terms(file_name, gpt_list, size):
    file_keywords = return_keyword_list(file_name)[:20000]
    file_list = ", ".join([word.lower() for word in file_keywords])

    list_compare_prompt = f"""I am going to give you two lists. The first list is called "GPT list" and the second list is called "Subject Terms List".
                        Based on the words in the "GPT list", find phrases in the "Subject Terms List" that describe similar contexts and themes. 
                        The result set should be comma delimited list without numbering.
                        This is the GPT list:{gpt_list}
                        This is the subject terms list: {file_list}
                        Order the list alphabetically from A-Z.
                        Limit the results to {result_size} of the most relevant phrases sourced from the "Subject Terms List"
                        Do not provide any additional commentary or feedback.
                        """
    return chatgpt(gpt_key, chat_model, list_compare_prompt)


# Define function to find missing keywords
def missing_keywords(keyword_list, icpsr_keywords):
    return ", ".join([item for item in keyword_list if item in icpsr_keywords])


def get_gpt_list(text_to_analyze):

    passage_prompt = f"""
              Here is a passage of text: {text_to_analyze}.Analyze the passage to understand the main context and themes. Return them
              in a comma delimited list. The themes and context descriptions should be no more than 3 words long and should not have special characters.
              Do not provide any additional commentary or feedback.
              """
    gpt_words = chatgpt(gpt_key, chat_model, passage_prompt)
    return [word.lower() for word in gpt_words]


# Define function to format data as HTML table


def format_data_as_html_table(data, headers):
    table_html = '<table border="1" style="border-collapse: collapse;">'
    table_html += '<tr>'
    for header in headers:
        table_html += f'<th style="padding: 8px; text-align: left;">{header}</th>'
    table_html += '</tr>'

    for row in data:
        table_html += '<tr>'
        for cell in row:
            if isinstance(cell, list):
                # Convert list items into an unordered list
                bullet_points = ''.join(f'<li>{item}</li>' for item in cell)
                cell = f'<ul>{bullet_points}</ul>'
            table_html += f'<td style="padding: 8px;text-align: left;">{cell}</td>'
        table_html += '</tr>'

    table_html += '</table>'
    return table_html



# Define main function to process form and generate results
def main(param, check_icpsr, check_elsst, check_mesh):
    gpt_list = get_gpt_list(param)
    icpsr_keywords = return_keyword_list("3")
    gpt_missing = missing_keywords(gpt_list, icpsr_keywords)

    if check_icpsr == True:
        icpsr_result = get_dictionary_terms("2", gpt_list, result_size)
    else:
        icpsr_result = "Not analyzed"
    if check_elsst == True:
        elsst_result = get_dictionary_terms("3", gpt_list, result_size)
        elsst_missing = missing_keywords(elsst_result, icpsr_keywords)
    else:
        elsst_result = "Not analyzed"
        elsst_missing = "Not analyzed"
    if check_mesh == True:
        mesh_result = get_dictionary_terms("1", gpt_list, result_size)
        mesh_missing = missing_keywords(mesh_result, icpsr_keywords)
    else:
        mesh_result = "Not analyzed"
        mesh_missing = "Not analyzed"

    data = [
        ["ChatGPT", gpt_list, gpt_missing],
        ["ICPSR", icpsr_result, ""],
        ["ELSST", elsst_result, elsst_missing],
        ["MESH", mesh_result, mesh_missing],
    ]

    headers = ["Source", "Suggested", "Keywords in ICPSR"]
    result = format_data_as_html_table(data, headers)
    return result


##################################################
################# FLASK ROUTES####################
##################################################

# Route to display the form
@app.route("/", methods=["GET", "POST"])
def index():
    results = ""
    if request.method == "POST":
        param = request.form.get("param", "")
        check_mesh = "mesh" in request.form
        check_icpsr = "icpsr" in request.form
        check_elsst = "elsst" in request.form

        results = main(param, check_icpsr, check_elsst, check_mesh)

    return render_template_string(
        """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Retrieve Suggested Keywords</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #00274C; /* Blue */
            color: #FFCB05; /* Maize */
            margin: 0;
            padding: 20px;
            text-align: center;
        }
        .container {
            display: flex;
            justify-content: space-between; /* This will place the content spaced out equally */
            height: calc(100vh - 40px); /* Subtract the padding of the body */
        }
        .form-container {
            flex: 1; /* Take up half the space */
            padding: 0 10px; /* Give some spacing */
        }
        .results-container {
            flex: 1; /* Take up the other half */
            background-color: #00274C; /* A different shade of blue */
            padding: 10px;
            border-radius: 5px;
            color: #FFCB05; /* Maize */
            height: calc(100vh - 40px); /* Full height */
            overflow-y: auto; /* Allow scrolling if content is too long */
        }
        textarea {
            width: 100%; /* Take full width of the container */
            height: 200px; /* Set a fixed height for textarea */
            margin-bottom: 20px;
        }
        .checkbox-group {
            margin-bottom: 20px;
        }
        button {
            background-color: #FFCB05; /* Maize */
            color: #00274C; /* Blue */
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #E6B905; /* Darker Maize */
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-container">
            <form action="/" method="POST">
                <label for="param"><h2>Enter Text To be Analyzed:</h2></label>
                <textarea id="param" name="param"></textarea>
                <h3>Check all sources that you would like to reference</h3>
                <div class="checkbox-group">
                    <input type="checkbox" id="icpsr" name="icpsr" value="true">
                    <label for="icpsr">ICPSR</label>
                    <input type="checkbox" id="mesh" name="mesh" value="true">
                    <label for="mesh">MESH</label>
                    <input type="checkbox" id="elsst" name="elsst" value="true">
                    <label for="elsst">ELSST</label>
                </div>
                <button type="submit">Submit</button>
            </form>
        </div>
        <div class="results-container">
            {% if results %}
                <div id="results">
                    <h2>Analysis Results:</h2>
                    <p>{{ results | safe }}</p>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>

    """,
        results=results,
    )


if __name__ == "__main__":

    load_dotenv()  # get client app variables to connect to the keyvault
    app.run(debug=True)  # run flask app
