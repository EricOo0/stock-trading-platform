import akshare as ak
try:
    df = ak.macro_china_pmi()
    print("Columns:", df.columns.tolist())
    print("Head:", df.head(1).to_dict('records'))
except Exception as e:
    print("Error:", e)
