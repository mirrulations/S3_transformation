# Proposed S3 Version 

## Raw Data Structure Overview 

-     <agency>
      └── <docket id>
          ├── binary-<docket id>
          │   ├── comments_attachments
          │   │   ├── <comment id>_attachement_<counter>.<extension>
          │   │   └── ...
          │   ├── documents_attachments
          │   │   ├── <document id>_attachement_<counter>.<extension>
          │   │   └── ...
          └── text-<docket id>
              ├── comments
              │   ├── <comment id>.json
              │   └── ...
              ├── docket
              │   ├── <docket id>.json
              |   └── ...
              ├── documents
              │   ├── <document id>.json
              │   ├── <document id>_content.htm
              │   └── ...


## Overall S3 Structure Overview


-       Mirrulations
            ├── Derived_data
            │   └── agency
            │       └── docketID
            │           ├── MoravianResearch
            │           │   └── projectName
            │           │       ├── comment
            │           │       ├── docket
            │           │       └── document
            │           ├── mirrulations
            │           │   ├── ai_summary
            │           │   │   ├── comment
            │           │   │   ├── comment_attachments
            │           │   │   └── document
            │           │   ├── entities
            │           │   │   ├── comment
            │           │   │   ├── comment_attachment
            │           │   │   └── document
            │           │   └── extracted_txt
            │           │       └── comment_attachment
            │           │           └── commentID_attachment.txt
            │           └── trotterf
            │               └── projectName
            │                   └── fileType
            │                       └── fileID.txt
            └── Raw_data
                └── old_structure_minus_extracted_txt
