
import akshare as ak
import pandas as pd

try:
    df = ak.macro_china_ppi_yearly()
    print("PPI Columns:", df.columns.tolist())
    print("First row:", df.iloc[0].to_dict())
except Exception as e:
    print(e)
