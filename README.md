# ICPSR Data Hydration

### Overview
Efficiently curating metadata with controlled terminology is a critical yet time-consuming task in
social science data management. Data depositors often provide insufficient metadata,
compelling data repository staff to extensively enhance the metadata. This process traditionally
involves navigating a wide array of controlled terms, a task demanding substantial time and
expertise, sometimes necessitating the creation of new terms.

Addressing these challenges, we introduce an innovative model employing Generative AI
technology (ChatGPT). This tool is engineered to significantly diminish the time required for
metadata curation for data repository staff while enhancing the accuracy of term matching. It
achieves this by rapidly analyzing text and extracting pertinent keywords from established
thesauri, including the ICPSR Subject Thesaurus, the European Language Social Science
Thesaurus (ELSST), and Library of Congress Subject Headings (LC SH), along with ChatGPT's
intelligent recommendations. This approach not only expedites the curation process but also
ensures heightened precision and recall in the results.

### Features
- **Batch Processing**: Efficiently handles multiple datasets in one go.
- **Targeted Data Hydration**: Supports custom scripts for fetching and processing specific datasets.
- **Flask Application**: A Flask-based web interface for managing hydration tasks.
- **Azure Integration**: Secure handling of secrets and credentials via Azure Key Vault.
- **OpenAI Integration**: Supports communication with OpenAI APIs to enhance data processing.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/cadenlpicard/icpsr_data_hydration.git
2. **Install Dependencies**
   pip install -r requirements.txt

### Usage

1. **Batch Hydration (script_batch.py)**:
  - The script_batch.py file manages the bulk processing of datasets:
  - It retrieves datasets in batches, processes them, and stores the hydrated data.
  python script_batch.py
  - Modify the script as needed to set batch size, dataset range, or custom data sources.
2. **Application Script (application.py):**
  - The application.py file serves as the main interface for specific data hydration tasks:
  - Web Application: It utilizes Flask to provide a web interface to manage and monitor hydration tasks.
  - Azure Key Vault Integration: Handles secure access to credentials, such as API keys and database connection details, via Azure Key Vault.
  - SQLAlchemy Integration: Uses SQLAlchemy for database interactions, making it easy to store and retrieve hydrated data.
    python application.py
    
### OpenAI Integration

The application interfaces with OpenAI’s API, allowing it to perform advanced text analysis, data generation, or model-based processing on the datasets. This can be useful for:

**Textual Data Analysis:** Using OpenAI models to analyze textual metadata or documents associated with the datasets.

**Data Augmentation:** Enhancing datasets with generated content, such as descriptions or labels.
To use OpenAI integration, ensure that the openai library is installed and that your OpenAI API key is stored securely (e.g., via environment variables). Modify the code to interact with OpenAI’s models, depending on the specific requirements of your hydration task.

**Example usage of OpenAI API in the script:**

```python
import openai

def process_with_openai(input_data):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Analyze the following data: {input_data}",
        max_tokens=100
    )
    return response['choices'][0]['text']

```
### File Structure
***application.py:*** Main script for managing hydration tasks, integrating with Azure for secure secret management, and using SQLAlchemy for database interactions.

***script_batch.py:*** Handles the batch processing and hydration of datasets.
***requirements.txt:*** Lists the required Python libraries for the project.


This project is licensed under the MIT License.
