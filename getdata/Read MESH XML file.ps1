# Create XmlReaderSettings with DTD processing enabled
$settings = New-Object System.Xml.XmlReaderSettings
$settings.DtdProcessing = [System.Xml.DtdProcessing]::Parse

# Define the path to your XML file
$xmlFilePath = 'C:\Users\mount\Downloads\desc2023.xml'

# Create an XmlReader instance with these settings
$reader = [System.Xml.XmlReader]::Create($xmlFilePath, $settings)


# Initialize a counter for the records
$count = 0

try {
    # Read through the file
    while ($reader.Read() -and $count -lt 100) {
        # Check if the current node is the element you're interested in
        if ($reader.NodeType -eq [System.Xml.XmlNodeType]::Element -and $reader.Name -eq 'yourElementName') {
            # Process the element
            $element = [System.Xml.Linq.XElement]::ReadFrom($reader)
            # Output the element, for example, its OuterXml
            Write-Output $element

            # Increment the counter
            $count++
        }
    }
} catch {
    Write-Error "An error occurred: $_"
} finally {
    # Ensure the reader is closed properly
    $reader.Close()
}

# The script ends here. The first 100 elements named 'yourElementName' have been processed.
