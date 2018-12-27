import pandas as pd
screener_file = 'screener 12272018.xls'
screener = pd.read_excel(screener_file)
print(screener.head())
