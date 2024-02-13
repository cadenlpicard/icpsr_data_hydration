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

# Set GLOBAL 
result_size = 10
TEMPERATURE = .5

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

# Define function to interact with ChatGPT
def chatgpt(gpt_key, chat_model, prompt,TEMPERATURE):
    openai.api_key = gpt_key
    response = openai.chat.completions.create(
        model=chat_model, messages=[{"role": "user", "content": prompt}], seed=1, temperature = TEMPERATURE
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
    return chatgpt(gpt_key, chat_model, list_compare_prompt,TEMPERATURE)


# Define function to find missing keywords
def missing_keywords(keyword_list, icpsr_keywords):
    return ", ".join([item for item in keyword_list if item in icpsr_keywords])


def get_gpt_list(text_to_analyze):

    passage_prompt = f"""
              Here is a passage of text: {text_to_analyze}.Analyze the passage to understand the main context and themes. Return them
              in a comma delimited list. The themes and context descriptions should be no more than 3 words long and should not have special characters.
              Do not provide any additional commentary or feedback.
              """
    gpt_words = chatgpt(gpt_key, chat_model, passage_prompt,TEMPERATURE)
    return [word.lower() for word in gpt_words[:10]]


# Define function to format data as HTML table


def format_data_as_html_table(data, headers):
    table_html = '<table border="1" style="border-collapse: collapse;">'
    table_html += '<tr>'
    for header in headers:
        table_html += f'<th style="padding: 8px; text-align: left;">{header}</th>'
    table_html += '</tr>'

    for row_index, row in enumerate(data):
        table_html += '<tr>'
        for cell_index, cell in enumerate(row):
            if isinstance(cell, list):
                # Start an unordered list for the cell content
                cell_content = "<ul>"
                for item in cell:
                    if has_related_words(item):
                        # Make the item clickable only if it's in the ICPSR column and has related words
                        cell_content += f'<li><a href="javascript:void(0);" onclick="fetchResults(\'{item}\')" style="color: #FFCB05; text-decoration: underline;">{item}</a></li>'
                    else:
                        # Just display the item as a list element
                        cell_content += f'<li>{item}</li>'
                cell_content += "</ul>"  # Close the unordered list
            else:
                # Display non-list cell content directly
                cell_content = cell
            table_html += f'<td style="padding: 8px;text-align: left;">{cell_content}</td>'
        table_html += '</tr>'

    table_html += '</table>'
    return table_html







# Define main function to process form and generate results
def main(param, check_icpsr, check_elsst, check_loc):
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
    if check_loc == True:
        loc_result = get_dictionary_terms("4", gpt_list, result_size)
        loc_missing = missing_keywords(loc_result, icpsr_keywords)
    else:
        loc_result = "Not analyzed"
        loc_missing = "Not analyzed"

    data = [
        ["ChatGPT", gpt_list, gpt_missing],
        ["ICPSR", icpsr_result, ""],
        ["ELSST", elsst_result, elsst_missing],
        ["LOC", loc_result, loc_missing],
    ]

    headers = ["Source", "Suggested", "Keywords in ICPSR"]
    result = format_data_as_html_table(data, headers)
    return result

def has_related_words(word):
    # SQL query to check if the word has related keywords
    sql_query = "SELECT dbo.has_related_keyword(:word)"
    
    # Execute SQL query
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query), {"word": word})
            row = result.fetchone() 
            if row and row[0] == 1:  
                return True
            else:
                return False
    except Exception as e:
        print(f"Error checking related words for '{word}': {e}")
        return False


##################################################
################# FLASK ROUTES####################
##################################################
# Flask route for AJAX request to get query results
@app.route('/query-results')
def query_results():
    word = request.args.get('word')
    sql_query = "exec dbo.return_associated_keywords :word"
    print(sql_query)
    with engine.connect() as connection:
        result = connection.execute(text(sql_query), {"word": word})
        rows = result.fetchall()

    table_html = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    table_html += '<tr><th>Associated Keyword (# of studies)</th></tr>'
    for row in rows:
        table_html += f'<tr><td>{row[1]}</td></tr>'
    
    table_html += '</table>'
    return table_html

# Route to display the form
@app.route("/", methods=["GET", "POST"])
def index():
    global TEMPERATURE
    results = ""
    if request.method == "POST":
        param = request.form.get("param", "")
        TEMPERATURE = float(request.form.get("temperature", 0.5))
        check_loc = "loc" in request.form
        check_icpsr = "icpsr" in request.form
        check_elsst = "elsst" in request.form

        results = main(param, check_icpsr, check_elsst, check_loc)

    return render_template_string(
        """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Retrieve Suggested Keywords</title>
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #00274C; /* U-M Blue */
        color: #FFCB05; /* U-M Maize */
        margin: 0;
        padding: 0;
        text-align: center;
    }

    .container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
        box-sizing: border-box;
    }

    .form-container, .results-container {
        flex-basis: 50%;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-radius: 8px;
        margin: 10px;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }

    .form-container {
        border-right: 2px solid #FFCB05;
    }

    .results-container {
        background-color: rgba(0, 39, 76, 0.85); /* U-M Blue with transparency */
        color: #FFCB05; /* U-M Maize */
        overflow-y: auto;
    }

    textarea, input[type="number"] {
        width: 100%;
        padding: 10px;
        margin-bottom: 20px;
        border: 1px solid #FFCB05;
        border-radius: 4px;
        background-color: #FFF;
        color: #333;
        box-sizing: border-box;
    }
    .banner {
            background-color: #FFCB05; /* U-M Maize */
            color: #00274C; /* U-M Blue */
            padding: 10px;
            text-align: center;
            font-weight: bold;
        }

        .form-container {
            margin-top: 2vh; /* Adjusted for centering before results */
        }

        #param {
            height: 350px; /* Larger text area */
        }

        #temperature {
            width: 60px; /* Smaller input for temperature */
            text-align: center;
            margin-bottom:20px;
            margin-top:20px;
        }
        
    .checkbox-group label {
        margin-right: 20px;
        color: #FFCB05;
        font-weight: bold;
    }

    input[type="checkbox"] {
        accent-color: #FFCB05;
    }

    button {
        background-color: #FFCB05; /* U-M Maize */
        color: #00274C; /* U-M Blue */
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }

    button:hover, button:focus {
        background-color: #E6B905; /* Darker Maize */
        outline: none;
    }

    h1, h2, h3 {
        font-weight: bold;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .container {
            flex-direction: column;
        }

        .form-container, .results-container {
            flex-basis: auto;
            margin-top:2vh;
            width: 100%;
        }
    
    }
    </style>
    <script>
        function showPopup(data) {
            const popup = document.createElement('div');
            popup.style.position = 'fixed';
            popup.style.left = '50%';
            popup.style.top = '50%';
            popup.style.transform = 'translate(-50%, -50%)';
            popup.style.backgroundColor = '#00274C'; // U-M Blue
            popup.style.color = '#FFCB05'; // U-M Maize
            popup.style.padding = '20px';
            popup.style.borderRadius = '8px';
            popup.style.border = '1px solid #FFCB05'; // U-M Maize
            popup.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
            popup.style.zIndex = '1000';

            const content = document.createElement('div');
            content.innerHTML = data;
            content.style.padding = '20px';
            content.style.borderBottom = '1px solid #FFCB05'; // U-M Maize

            const closeButton = document.createElement('button');
            closeButton.textContent = 'Close';
            closeButton.style.padding = '10px 20px';
            closeButton.style.marginTop = '10px';
            closeButton.style.border = 'none';
            closeButton.style.borderRadius = '4px';
            closeButton.style.backgroundColor = '#FFCB05'; // U-M Maize
            closeButton.style.color = '#00274C'; // U-M Blue
            closeButton.style.cursor = 'pointer';
            closeButton.style.fontWeight = 'bold';
            closeButton.style.textTransform = 'uppercase';
            closeButton.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.2)';
            closeButton.onmouseover = function() {
                this.style.backgroundColor = '#E6B905'; // Darker Maize
            };
            closeButton.onmouseout = function() {
                this.style.backgroundColor = '#FFCB05'; // U-M Maize
            };
            closeButton.onclick = function() {
                document.body.removeChild(popup);
            };

            popup.appendChild(content);
            popup.appendChild(closeButton);
            document.body.appendChild(popup);
    }


        function fetchResults(word) {
            fetch(`/query-results?word=${word}`)
                .then(response => response.text())
                .then(html => showPopup(html))
                .catch(error => console.error('Error fetching details:', error));
        }
    </script>
</head>
<body>
    <div class="banner">For Research Purposes Only</div>
    <div class="container">
        <div class="form-container">
            <form action="/" method="POST">
                <label for="param"><h2>Enter Text To be Analyzed:</h2></label>
                <textarea id="param" name="param"></textarea>
                <div class="checkbox-group">
                    <input type="checkbox" id="icpsr" name="icpsr" value="true">
                    <label for="icpsr">ICPSR</label>
                    <input type="checkbox" id="loc" name="loc" value="true">
                    <label for="loc">Library of Congress</label>
                    <input type="checkbox" id="elsst" name="elsst" value="true">
                    <label for="elsst">ELSST</label>
                </div>
                <div></div>
                <div class="temperature-input">
                    <label for="temperature">Temperature:</label>
                    <input type="number" id="temperature" name="temperature" min="0" max="1" step="0.01" value="0.5">
                </div>
                <button type="submit">Submit</button>
            </form>
        </div>
        <div class="results-container" style="display: {% if results %} block {% else %} none {% endif %};">
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
