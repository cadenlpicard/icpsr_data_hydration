import re
import csv
import locationtagger
from prettytable import PrettyTable
from nltk.corpus import wordnet
import pandas as pd

##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
## Give the geographical regions referenced in the following summary about a study:
## can you provide me a list with the scope of the geographical region such as country, state, city etc..##




##define threshold for similarity

threshold = 1
record_set = 20


###############################################################################################
###############################################################################################

def read_csv(file_name):
    with open(file_name, 'r') as file:
        reader = csv.reader(file)
        return [row[0] for row in reader]
    
###############################################################################################
###############################################################################################

def read_vars(file_name):

    csv.field_size_limit(2**31 - 1)
    with open(file_name, 'r') as file:
        reader = csv.reader(file,delimiter=',',quotechar="|")
        
        return [row[5] for idx, row in enumerate(reader) if idx < record_set]  

###############################################################################################
###############################################################################################

def replace_double_line_breaks(file_name):
    with open(file_name, 'r') as file:
        content = file.read()

    content = content.replace('\n\n', '\n')

    with open(file_name, 'w') as file:
        file.write(content)

# replace_double_line_breaks("VAR_CSV_OUTPUT_SAMPLE.lst")

###############################################################################################
###############################################################################################

def process_text(text, subject_matter_terms):
    subject_matter_found = {}
    
    words = re.split(r'\W+', str(text))  # Split field into words
    for word in words:
        if word in subject_matter_terms:
            if word in subject_matter_found:
                subject_matter_found[word] += 1
            else:
                subject_matter_found[word] = 1

    return subject_matter_found

###############################################################################################
###############################################################################################

def get_geo(text):

    # extracting entities.
    place_entity = locationtagger.find_locations(text = str(text))
    
    country = place_entity.countries
    region = place_entity.regions
    city = place_entity.cities

    return country, region, city

###############################################################################################
###############################################################################################

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)



###############################################################################################
###############################################################################################

def get_similarity_score(word1, word2):
    word1 = wordnet.synsets(word1)[0]  # get the first synset
    word2 = wordnet.synsets(word2)[0]  # get the first synset
    score = word1.path_similarity(word2) 
    return score


###############################################################################################
###############################################################################################

def main():
    
    ## SUBJECT TERMS ##
    subject_matter_terms = read_csv("search_terms.csv") 

    ## LOAD VARIABLES FROM FILE ###
    ##text = read_vars("VAR_CSV_OUTPUT_SAMPLE.lst")  
    
    text ='''This data collection contains the results of a sample survey of University of Michigan (U-M)
    , Ann Arbor, faculty, staff, and students meant to represent the full diversity of the community and to capture information 
    and perceptions on demographics, climate, institutional commitment and inclusive and equitable treatment, departmental norms
    , intergroup interactions, and discrimination. With input from committees of students, faculty, and staff
    , the survey instrument was developed collaboratively by the U-M Office of the Provost
    , U-M's Survey Research Center, and administered by SoundRocket, an external social science survey research company
    . The instrument was delivered as a web survey, and several notifications and reminders were used to encourage completion
    , as well as an incentive. These notifications and reminders were delivered in phases.'''


    # Create a PrettyTable
    subject_table = PrettyTable()

    # Specify the Column Names while initializing the Table
    subject_table.field_names = ["Subject Matter Term", "Count", "Similar Words"]


    ### GET GEOGRAPHY DATA ####
    country, region, city = get_geo(text)
    print("Countries: ", country)
    print("Regions: ", region)
    print("Cities: ", city)

    subject_matter_found = process_text(text, subject_matter_terms)

    # Sorting the dictionary by values in descending order and iterating over items
    for term, count in sorted(subject_matter_found.items(), key=lambda item: item[1], reverse=True):
        # Get the top 3 most similar words for the current term
        similar_words = get_synonyms(term)
        for word in similar_words:  
            score = get_similarity_score(term, word)
            if score < threshold or term.lower() == word.lower():
                similar_words.remove(word)
                  
        # Add a row to the table
        subject_table.add_row([term, count, ", ".join(similar_words)])
    
    print(subject_table)

if __name__ == "__main__":
    main()
