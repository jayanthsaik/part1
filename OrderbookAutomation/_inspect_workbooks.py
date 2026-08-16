import pandas as pd
from pathlib import Path

# Resolve the data directory relative to this script's location so the
# project works on any machine, regardless of where it is checked out.
ROOT = Path(__file__).resolve().parent.parent

paths = [
    ROOT / 'Headers.xlsx',
    ROOT / 'POB.xlsx',
    ROOT / 'sales_summ.xlsx',
    ROOT / 'Buying_groups.xlsx',
]
for path in paths:
    print(f'FILE: {path.name}')
    try:
        xls = pd.ExcelFile(path)
    except Exception as exc:
        print(f'ERROR: {exc}')
        continue
    print('SHEETS:', xls.sheet_names)
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(path, sheet_name=sheet, header=None)
        except Exception as exc:
            print(f'SHEET ERROR {sheet}: {exc}')
            continue
        print(f'SHEET: {sheet}')
        print(df.head(12).to_string(index=True, header=False))
    print('---')
