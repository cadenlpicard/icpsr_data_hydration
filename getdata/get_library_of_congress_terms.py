
import requests
import csv


def create_url_library_of_congress(URI):
    
    file_type = '.json'
    base_url = 'https://id.loc.gov'
    #print(URI)
    url = base_url.strip()+URI[0].strip()+file_type.strip()  
    #print(url)
    return url


def generate_api_content_library_of_congress(url):
    r = requests.get(url)
    if r.status_code ==200:
        data=r.json()
        for item in data:
            if "@type" in item and "http://www.loc.gov/mads/rdf/v1#TopicElement"  in item["@type"]:
                if "http://www.loc.gov/mads/rdf/v1#elementValue" in item:
                    value = item["http://www.loc.gov/mads/rdf/v1#elementValue"][0]["@value"]
                    #print(value)
                    return(value)
                
def write_loc_terms(output_file, uri_file):
          
    with open(uri_file) as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                api_content = generate_api_content_library_of_congress(create_url_library_of_congress(row))
                if api_content != None:
                    with open(output_file,'a', encoding = "utf-8") as f1:
                            writer=csv.writer(f1, delimiter=',',lineterminator='\n',)
                            writer.writerow(api_content) 
                            
def create_unique_file(file_name):
    
    file = file_name
    # Step 1: Read the file and store unique values
    unique_keywords = set()
    with open(file, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, delimiter='\t',lineterminator='\n')
        header = next(csvreader)  # Skip the header row
        for row in csvreader:
            keyword = row[0].strip()
            unique_keywords.add(keyword)

    # Step 2: Overwrite the file with unique values
    # with open(file, 'w', newline='', encoding='utf-8') as csvfile:
    #     csvwriter = csv.writer(csvfile, delimiter=',')
    #     csvwriter.writerow(['keyword'])  # Write the header
    #     for keyword in sorted(unique_keywords):
    #         csvwriter.writerow([keyword])   
    return(unique_keywords)             

def main():
    
    write_loc_terms('LOC_Terms.csv', 'library_of_congress_parsed.csv')

                  

if __name__ == "__main__":
    main()
