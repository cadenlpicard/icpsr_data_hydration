from xml.etree import cElementTree as ET
import re
import requests
import json
import csv
elsst_file = 'ELSST_Terms.csv'

def get_json_from_web():
    
    url = "https://thesauri.cessda.eu/rest/v1/elsst-4/data?lang=en"
    r = requests.get(url)
    with open('ELSST.json', 'w',encoding="utf-8" ) as fd:
        fd.write(r.text)                


def split_terms():
    
    pattern = r"https://elsst.cessda.eu/id/4/.{36}"
    f = open('ELSST.json', "r", encoding ="utf-8")
    data = json.loads(f.read())
    ls= re.findall(pattern, str(data))
    return(ls)


def create_url(call_type,URI,language="en"):

    lang_param = '&lang=' + language
    if call_type == 'label':
        base_url = r'https://thesauri.cessda.eu/rest/v1/elsst-4/label?uri='
    elif call_type == 'related':
        base_url = r'https://thesauri.cessda.eu/rest/v1/elsst-4/related?uri='

    url = base_url.strip()+URI.strip()+lang_param.strip()  
    return url


def generate_api_content(call_type,url):
    
    r = requests.get(url)
    record = r.text
    if len(record) > 0:
        try:
            json_records = json.loads(record) 
            if call_type == "related":
                labels = json_records["related"]
                return labels
                
            elif call_type == "label":
                labels = json_records["prefLabel"]
                return labels            
        except:
            error_message = "Error: " +  r + " : " + call_type + " - " + url
            return error_message
    return labels

    
def get_elsst_terms(call_type):
    term_list = split_terms() 
    i=0
    while i<=len(term_list):
        print(len(term_list))
        for term in term_list:
            if "}]" not in term and "@" not in term:
                url = create_url(call_type,term)
                #print(url);  
                api_content = generate_api_content(call_type, url)
                with open(elsst_file,'a') as f1:
                    writer=csv.writer(f1, delimiter='\t',lineterminator='\n',)
                    writer.writerow(api_content)
                    print(api_content)
        i += 1
        return('Records inserted:', i)
    
    
def main():
    
    get_elsst_terms('label')

                
if __name__ == "__main__":
    main()
