import pandas as pd

kodlar=pd.read_csv("bist_artanlar_yfinance.csv")
kodlar_list=kodlar["Hisse"].tolist()
for şirket in kodlar_list:
    print(şirket)
