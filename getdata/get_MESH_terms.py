import xml.etree.ElementTree as ET
import csv

# Path to your XML file
xml_file = 'desc2023.xml'

# Parse the XML file
tree = ET.parse(xml_file)
root = tree.getroot()

# Define the path for your CSV file
csv_file = 'MESH_Terms.csv'

# Open the CSV file for writing
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Write the header to the CSV file
    writer.writerow(['keyword'])

    # Iterate through each DescriptorRecord in the XML
    for descriptor in root.findall('.//DescriptorRecord'):
        descriptorName = descriptor.find('DescriptorName/String').text if descriptor.find('DescriptorName/String') is not None else ''

        # Write the data to the CSV file
        writer.writerow([descriptorName])
