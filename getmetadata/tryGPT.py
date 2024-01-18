import openai
import pandas as pd
from tabulate import tabulate

######################################################
################# GLOBAL VARIABLES####################
######################################################

key = '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'
chat_model = "gpt-4-1106-preview" 

result_size = 10

text_to_analyze = '''This dataset contains two measures designed to be used 
in tandem to characterize United States census tracts, originally developed for 
use in stratified analyses of the Diabetes Location, Environmental Attributes,
and Disparities (LEAD) Network. The first measure is a 2010 tract-level community 
type categorization based on a modification of Rural-Urban Commuting Area (RUCA) Codes 
that incorporates census-designated urban areas and tract land area, with five categories:
higher density urban, lower density urban, suburban/small town, rural, and undesignated (McAlexander, et al., 2022).
The second measure is a neighborhood social and economic environment (NSEE) score,
a community-type stratified z-score sum of 6 US census-derived variables, with sums scaled between 0 and 100,
computed for the year 2000 and 2010. A tract with a higher NSEE z-score sum indicates more socioeconomic 
disadvantage compared to a tract with a lower z-score sum. Analysts should not compare NSEE scores across
LEAD community types, as values have been computed and scaled within community type.'''

icpsr_file = 'data\search_terms.csv'
loc_file = 'data\LOC_terms.csv'
elsst_file = 'data\ELSST_Terms.csv'
mesh_file = 'data\MESH_Terms.csv'

######################################################
################# CHATGPT ###########################
######################################################

def chatgpt(key, chat_model, prompt):
  

  openai.api_key = key  
  response = openai.chat.completions.create(
  model=chat_model,  
  messages=[{
              "role": "user"
             , "content": prompt 
            }
            ],
  seed = 1
  )
  responses = response.choices[0].message.content.strip()
  gpt_list = list(responses.split(","))
  return(gpt_list)

######################################################
################# KEYWORD LISTS ######################
######################################################

def return_keyword_list(file_name, header_name ='keywords'):
  df = pd.read_csv(file_name)
  keywords = df[header_name].tolist()
  lower_keywords = [word.lower() for word in keywords]
  return lower_keywords

######################################################
################# Look at dictionaries################
######################################################

def get_dictionary_terms(file_name, gpt_list, result_size):
    
  file_keywords = return_keyword_list(file_name)
  limited_list = file_keywords[:20000]
  lowerfile_words = [word.lower() for word in limited_list]
  file_list = ','.join(lowerfile_words)
  
  list_compare_prompt = f'''I am going to give you two lists. The first list is called "GPT list" and the second list is called "Subject Terms List".
                        Based on the words in the "GPT list", find phrases in the "Subject Terms List" that describe similar contexts and themes. 
                        The result set should be comma delimited list without numbering.
                        This is the GPT list:{gpt_list}
                        This is the subject terms list: {file_list}
                        Order the list alphabetically from A-Z.
                        Limit the results to {result_size} of the most relevant phrases sourced from the "Subject Terms List"'''
  
  #print(list_compare_prompt)
  
  gpt_compare = chatgpt(key, chat_model,list_compare_prompt)
  gpt_compare_str = '\n'.join(gpt_compare) 
  
  return_results = gpt_compare_str
  return(return_results)
  
  
def missing_keywords(keyword_list,icpsr_keywords):
  
  missing_keywords= [item for item in keyword_list.split("\n") if item not in icpsr_keywords]
  missing_keywords = "\n".join(missing_keywords)
  return(missing_keywords)
  
def get_gpt_list(text_to_analyze):
  
  passage_prompt = f'''
              Here is a passage of text: {text_to_analyze}.Analyze the passage to understand the main context and themes. Return them
              in a comma delimited list. The themes and context descriptions should be no more than 3 words long and should not have special characters.
              '''
  
  gpt_words = chatgpt(key, chat_model,passage_prompt)   
  lower_gpt_words = [word.lower() for word in gpt_words]
  gpt_list = '\n'.join(lower_gpt_words) 
  return(gpt_list)
       
##################################################
################# MAIN ###########################
##################################################
def main():
    
    gpt_list = get_gpt_list(text_to_analyze)

      
    # get results #  
    icpsr_keywords = return_keyword_list(icpsr_file)
    icpsr_result = get_dictionary_terms(icpsr_file, gpt_list, result_size)
    #loc_result = get_dictionary_terms(loc_file, gpt_list, result_size)
    elsst_result = get_dictionary_terms(elsst_file, gpt_list, result_size)
    mesh_result = get_dictionary_terms(mesh_file, gpt_list, result_size)
    
    #find missing #
    elsst_missing = missing_keywords(elsst_result,icpsr_keywords)
    gpt_missing = missing_keywords(gpt_list,icpsr_keywords)
    mesh_missing = missing_keywords(mesh_result,icpsr_keywords)
    
    data = [
            ["ChatGPT", gpt_list, gpt_missing]
          , ["ICPSR", icpsr_result, ""]
          , ["ELSST", elsst_result, elsst_missing]
          , ["MESH", mesh_result, mesh_missing]
          ]
    headers = ["Source", "Suggested", "Missing from ICPSR"]

    print(tabulate(data, headers, tablefmt="grid"))
    

        
if __name__ == "__main__":
    main()

