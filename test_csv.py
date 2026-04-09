import pandas as pd
import io

csv_data = """Name,Path,Data Type,Logical Address,Comment,Hmi Visible,Hmi Accessible,Hmi Writeable,Typeobject ID,Version ID
Start_Button,,Bool,%I0.0,Start Button,True,True,True,,
"""

try:
    df = pd.read_csv(io.StringIO(csv_data), dtype=str, skipinitialspace=True)
    df = df.fillna('')
    print('Columns:', df.columns.tolist())
    print(df.to_dict('records'))
except Exception as e:
    print('Error:', e)
