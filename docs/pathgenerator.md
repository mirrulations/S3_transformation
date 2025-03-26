# Documenattion: Changes made to pathgenerator.py(mirrulations path generator)

# Overview
This script handles determining the path of a file when retrieved from regulations.gov and saved into the Mirrulations S3 bucket. The script was updated to align with the new data structure, where raw data is saved in the /raw-data folder.

# Key Changes:
## 1. Introduction of the PathGenerator Class
The PathGenerator class was updated to classify files into the correct directory based on the new data structure. It extracts information from dockets, documents, or comments JSON files and generates paths accordingly.

## 2. Updated Methods
The following methods were updated to align with the new data structure and improve error handling:

`get_path(self, json)`
- Checks if the data key exists in the JSON and calls the appropriate path generator method based on the type key.
- Prepends `/raw-data` to the generated path.

`get_document_htm_path(self, json):`
- If a document is an htm file it prepends `/raw-data` to the generated path

`_parse_attachment_path(self, json, file_format, attachments)`
- If a file is an comment attachment their path is generated with `raw-data` prepended.

5. New Data Structure
The updated paths follow the new data structure:

Dockets: 
- /raw-data/{agencyId}/{docketId}/text-{docketId}/docket/{docketId}.json

Documents: 
- /raw-data/{agencyId}/{docketId}/text-{docketId}/documents/{itemId}.json
- /raw-data/{agencyId}/{docketId}/text-{docketId}/documents/{itemId}_content.htm

Comments: 
- /raw-data/{agencyId}/{docketId}/text-{docketId}/comments/{itemId}.json

Attachments: 
- /raw-data/{agencyId}/{docketId}/binary-{docketId}/comments_attachments/{attachment_name}
