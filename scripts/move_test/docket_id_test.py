import re

# Example docket IDs to test
docket_ids = [
    "FDA-2025-N-4611", 
    "EPA-R08-OAR-2025-0625",
    "FWS-R3-ES-2025-0137", 
    "Agency-Region-2025-12345", 
    "FWS-R3-ES-2024-9999",
    "FDA-2019-N-4611"
]

# Regex pattern to match docket IDs for 2025
pattern = re.compile(r'^[A-Za-z]+(?:-[A-Za-z0-9]+)*-2025-[A-Za-z0-9-]+$')

for docket_id in docket_ids:
    if pattern.match(docket_id):
        print(f"Match: {docket_id}")
    else:
        print(f"No match: {docket_id}")

