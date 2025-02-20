import re

# Sample docket IDs to test against
docket_ids = [
    "BIS/BIS-2025-0047/binary-BIS-2025-0047/comments_attachments/BIS-2025-0047-0002_attachment_1.docx",
    "BIS/BIS-2025-0047/binary-BIS-2025-0047/comments_attachments/BIS-2025-0047-0003_attachment_1.pdf",
    "BIS/BIS-2025-0047/text-BIS-2025-0047/docket/BIS-2025-0047_docket.txt",
    "XYZ/ABC-2025-1234/binary-ABC-2025-1234/comments_attachments/ABC-2025-1234-001_attachment.pdf",
    "InvalidKeyWithoutDocketID/attachment.txt"
]

# Regex pattern to match docket IDs with year 2025
DOCKET_PATTERN = re.compile(r'([A-Za-z0-9\-]+-2025-[A-Za-z0-9\-]+)')

# Test extraction
def test_docket_extraction(docket_ids):
    for docket_id in docket_ids:
        match = DOCKET_PATTERN.search(docket_id)
        if match:
            found_docket_id = match.group(1)  # Capture the first group, which is the docket ID
            print(f"Found docket ID: {found_docket_id}")
        else:
            print(f"No docket ID found for year 2025 in: {docket_id}")

# Run the test
test_docket_extraction(docket_ids)

