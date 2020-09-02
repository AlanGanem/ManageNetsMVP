import pandas as pd

def read_file(file_path):
    try:
        file = pd.read_csv(file_path)
    except:
        file = pd.read_excel(file_path)
    return file
