import pandas as pd
import tempfile
import time

from app.utils.database.connection import Neo4jConnection

class Neo4JGraphBuilder:
    """Import CSV into Neo4J database"""

    def __init__(self):
        self.db = Neo4jConnection()

    def _drop_columns(self, df):
        df = df.drop(['Currency', 'Phone Numbers', 'Bank Numbers', 'Dates', 'Vehicles', 'PAN', 'Aadhar', 'Emails', 'URLs', 'IPs', 'Passport', 'Associates', 'Source Link', 'Lat', 'Long', 'Threshold', 'Sentiment', 'Count'], axis=1)
        return df        
    
    def _create_node_constraints(self):
        self.db.query('CREATE CONSTRAINT Name IF NOT EXISTS ON (n:Name) ASSERT p.name IS UNIQUE')
        self.db.query('CREATE CONSTRAINT Org IF NOT EXISTS ON (o:Org) ASSERT o.org IS UNIQUE')
        self.db.query('CREATE CONSTRAINT Keyword IF NOT EXISTS ON (k:Keyword) ASSERT k.keyword IS UNIQUE')
        self.db.query('CREATE CONSTRAINT Source IF NOT EXISTS ON (s:Source) ASSERT s.source IS UNIQUE')

    def add_keywords(self, keywords):
        # Adds category nodes to the Neo4j graph.
        # print(keywords)
        query = '''
                UNWIND $rows AS row
                MERGE (k:Keywords {keywords: row.keywords})
                RETURN count(*) as total
                '''
        return self.db.query(query, parameters = {'rows':keywords.to_dict('records')})


    def _create_nodes(self, nodes, node_label, property_key, node_label_key):
        # Adds nodes to the Neo4j graph dynamically based on the node label and property key.
        query = f'''
                UNWIND $rows AS row
                MERGE ({node_label_key}:{node_label} {{{property_key}: row.{property_key}}})
                RETURN count(*) as total
                '''
        return self.db.query(query, parameters={'rows': nodes.to_dict('records')})
    
    def _insert_data(self, query, rows, batch_size = 2):
        # Function to handle the updating the Neo4j database in batch mode.
        
        total = 0
        batch = 0
        start = time.time()
        result = None
        print(len(rows))
        print(batch_size)
        
        while batch * batch_size < len(rows):
            print(rows[batch*batch_size:(batch+1)*batch_size].to_dict('records'))
            res = self.db.query(query, 
                            parameters = {'rows': rows[batch*batch_size:(batch+1)*batch_size].to_dict('records')})
            print(res)
            total += res[0]['total']
            batch += 1
            result = {"total":total, 
                    "batches":batch, 
                    "time":time.time()-start}
            print(result)
            
        return result
        
    def _create_relations(self, rows):
        # Adds Source nodes and (:Source)-->(:Name),
        # (:Source)-->(:Org) and (:Source)-->(:Keyword)
        #  relationships to the Neo4j graph as a batch job.
        
        query = '''
        UNWIND $rows as row
        MERGE (s:Source {id: row.source}) ON CREATE SET s.source = row.source
        
        // connect keywords
        WITH row, s
        UNWIND row.Keywords AS keywords
        MATCH (k:Keywords {keywords: keywords})
        MERGE (s)-[:USED_KEYWORDS]->(k)
        
        // connect org
        WITH distinct row, s // reduce cardinality
        UNWIND row.Organizations AS org
        MATCH (o:Org {org: org})
        MERGE (s)-[:WORKS_FOR]->(o)

        // connect names
        WITH distinct row, s // reduce cardinality
        UNWIND row.Names AS names
        MATCH (n:Names {names: names})
        MERGE (s)-[:NAMES_FOUND]->(n)
        RETURN count(distinct s) as total
        '''
        
        return self._insert_data(query, rows)



    def upload_to_neo4j_database(self, file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(file)
            tmp_file_path = tmp_file.name
        df = pd.read_csv(tmp_file_path)
        # df = self._drop_columns(df)

        names = pd.DataFrame(df[['Names']])
        names.rename(columns={'Names':'names'},
                        inplace=True)
        names = names.explode('names').drop_duplicates(subset=['names'])

        org = pd.DataFrame(df[['Organizations']])
        org.rename(columns={'Organizations':'org'},
                        inplace=True)
        org = org.explode('org').drop_duplicates(subset=['org'])

        keywords = pd.DataFrame(df[['Keywords']])
        keywords.rename(columns={'Keywords':'keywords'},
                        inplace=True)
        keywords = keywords.explode('keywords').drop_duplicates(subset=['keywords'])

        # self._create_node_constraints()

        ## Add keywords
        keyw = self.add_keywords(keywords)
        print("test")
        print(keyw)
        ## Add Organizations
        self._create_nodes(org, 'Org', 'org', 'o')

        ## Add Names
        self._create_nodes(names, 'Names', 'names', 'n')

        ## Create nodes relations
        self._create_relations(df)

        return {"success": 200, "message": "successfully uploaded"}        





