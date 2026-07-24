import pandas as pd
import json

excel_file = r'c:\Users\volap\Desktop\New folder\KrishilQ\docs\Automation_Test_Report.xlsx'

try:
    df = pd.read_excel(excel_file, sheet_name='Test Results')
    
    # Filter only failed tests
    failed_tests = df[df['Status'] == 'FAILED']
    
    failures = []
    for _, row in failed_tests.iterrows():
        failures.append({
            'ID': row['Test ID'],
            'Module': row['Module']
        })
        
    out_file = r'c:\Users\volap\Desktop\New folder\KrishilQ\failed_tests.json'
    with open(out_file, 'w') as f:
        json.dump(failures, f, indent=2)
        
    print(f"Successfully extracted {len(failures)} failed tests to {out_file}")
except Exception as e:
    print(f"Error: {e}")
