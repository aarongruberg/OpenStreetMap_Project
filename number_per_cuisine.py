# This is one of my sql queries. It finds the count of each cuisine value that occurs more than once.
# I excluded things like ice_cream and juice from my query because I was only interested in savory food.

import sqlite3

# Fetch records from either mission_district.db
db = sqlite3.connect("mission_district.db")
c = db.cursor()


QUERY = """
SELECT both.value, COUNT(both.value)
from (SELECT *
from Nodes_Tags
where Nodes_Tags.key = 'cuisine'
UNION
SELECT *
from Ways_Tags
where Ways_Tags.key = 'cuisine') as both
GROUP BY both.value
HAVING COUNT(both.value) > 1
AND both.value != 'coffee_shop' 
AND both.value != 'ice_cream'
AND both.value != 'juice' 
ORDER BY COUNT(both.value)
DESC;"""

c.execute(QUERY)
rows = c.fetchall()

import pandas as pd    
df = pd.DataFrame(rows)

# Print the entire dataframe

pd.set_option('display.max_rows', len(df))

print df
