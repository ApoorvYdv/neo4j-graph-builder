import pandas as pd

from add_categories import add_categories, add_authors
from node_and_edges import add_papers
from data_cleaning import get_cleaned_df
from load_file import get_df
from connect import Neo4jConnection

df = get_df()
cleaned_df = get_cleaned_df(df)

categories = pd.DataFrame(df[['category_list']])
categories.rename(columns={'category_list':'category'},
                  inplace=True)
categories = categories.explode('category') \
                       .drop_duplicates(subset=['category'])

authors = pd.DataFrame(df[['cleaned_authors_list']])
authors.rename(columns={'cleaned_authors_list':'author'},
               inplace=True)
authors=authors.explode('author').drop_duplicates(subset=['author'])

add_categories(categories)
add_authors(authors)
add_papers(df)

query_string = '''
MATCH (c:Category) 
RETURN c.category_name, SIZE(()-[:IN_CATEGORY]->(c)) AS inDegree 
ORDER BY inDegree DESC LIMIT 20
'''
conn = Neo4jConnection()
top_cat_df = pd.DataFrame([dict(_) for _ in conn.query(query_string)])
top_cat_df.head(20)
print(df)