import json

def get_json(File_Name: str):
    "Import json file: read"
    with open(File_Name, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def set_json(File_Name: str, value: any):
    "Save json file to value."
    with open(File_Name, 'w') as f:
        json.dump(value, f)