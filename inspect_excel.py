import pandas as pd
from pathlib import Path
for path in [Path('raw_OB.xlsx'), Path('Mat_Desc,_MOQ_,_Material_#.xlsx'), Path('07-30_inv.xlsx'), Path('Open_Order_Summary.xlsx')]:
    print('FILE', path.name)
    xls = pd.ExcelFile(path)
    print('SHEETS', xls.sheet_names)
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        print('SHEET', sheet, 'COLUMNS', list(df.columns))
        print(df.head(3).to_string(index=False))
        print('---')
    print('====')
