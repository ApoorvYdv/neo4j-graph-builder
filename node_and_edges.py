from add_categories import insert_data


def add_papers(rows, batch_size=5000):
   # Adds paper nodes and (:Author)--(:Paper) and 
   # (:Paper)--(:Category) relationships to the Neo4j graph as a 
   # batch job.
 
   query = '''
   UNWIND $rows as row
   MERGE (p:Paper {id:row.id}) ON CREATE SET p.title = row.title
 
   // connect categories
   WITH row, p
   UNWIND row.category_list AS category_name
   MATCH (c:Category {category: category_name})
   MERGE (p)-[:IN_CATEGORY]->(c)
 
   // connect authors
   WITH distinct row, p // reduce cardinality
   UNWIND row.cleaned_authors_list AS author
   MATCH (a:Author {name: author})
   MERGE (a)-[:AUTHORED]->(p)
   RETURN count(distinct p) as total
   '''
 
   return insert_data(query, rows, batch_size)