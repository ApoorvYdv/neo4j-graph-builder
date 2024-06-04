import pandas as pd

def get_author_list(line):
    # Cleans author dataframe column, creating a list of authors in the row.
    return [e[1] + ' ' + e[0] for e in line]


def get_category_list(line):
    # Cleans category dataframe column, creating a list of categories in the row.
    return list(line.split(" "))

def get_cleaned_df(df):
    df['cleaned_authors_list'] = df['authors_parsed'].map(get_author_list)
    df['category_list'] = df['categories'].map(get_category_list)
    df = df.drop(['submitter', 'authors', 
                'comments', 'journal-ref', 
                'doi', 'report-no', 'license', 
                'versions', 'update_date', 
                'abstract', 'authors_parsed', 
                'categories'], axis=1)
    return df