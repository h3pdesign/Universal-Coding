import pandas as pd
data_files = [
    "ap_2010.csv",
    "class_size.csv",
    "demographics.csv",
    "graduation.csv",
    "hs_directory.csv",
    "sat_results.csv"
]

# Dictionary to hold all DataFrames
data = {}

# Read each CSV and store in the dictionary
for file in data_files:
    key = file.replace(".csv","")    # remove.csv for dictionary key
    path = f"schools/{file}"    # build full path
    data[key]= pd.read_csv(path)
    
    print(data.keys())
print(f"Loaded {file} with shape {data[key].shape}")		
print(data["sat_results"].head())

