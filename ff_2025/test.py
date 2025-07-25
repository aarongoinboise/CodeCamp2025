import pandas as pd

url = 'https://www.pro-football-reference.com/years/2020/coaches.htm'
df = pd.read_html(url)[0]
print(df)