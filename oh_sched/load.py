import pandas as pd


def extract_csv(f_csv):
    df = pd.read_csv(f_csv)

    # drop duplicates email (take latest)
    df.sort_values('Timestamp', inplace=True)
    df.drop_duplicates(subset=df.columns[1], keep='last', inplace=True)

    # map all numeric columns to numbers (inputs might be of form "4 (
    # available and most preferred)")
    num_map = {'4 (available and most preferred)': 4,
               '1 (available if need be)': 1}

    def to_int(x):
        if isinstance(x, str):
            if x in num_map:
                x = num_map[x]
            else:
                x = int(x)
        return x

    df.iloc[:, 3:] = df.iloc[:, 3:].map(to_int)

    email_list = df.iloc[:, 1].to_list()
    name_list = df.iloc[:, 2].to_list()
    oh_list = df.columns[3:].to_list()
    prefs = df.iloc[:, 3:].values.astype(float)
    return prefs, email_list, name_list, oh_list


if __name__ == '__main__':
    extract_csv('oh_response.csv')