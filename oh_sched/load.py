import pandas as pd


def extract_csv(f_csv):
    df = pd.read_csv(f_csv)

    # drop duplicates email (take latest)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.sort_values('Timestamp', inplace=True)
    df.drop_duplicates(subset=df.columns[1], keep='last', inplace=True)

    # extract necessary info
    email_list = df.iloc[:, 1].to_list()
    name_list = df.iloc[:, 2].to_list()
    oh_list = df.columns[3:].to_list()
    prefs = df.iloc[:, 3:].values.astype(float)

    return prefs, email_list, name_list, oh_list
