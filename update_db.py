# -*- coding: latin-1 -*-

import sqlite3
import pandas as pd

conn = sqlite3.connect('caves.db')
c = conn.cursor()
# si la table n'existe pas, on la crée
try:
    c.execute('''CREATE TABLE caves (id text, title text, price real, url text, type text, city text, surface real, description text, date_creation text, date_suppression text)''')
except:
    pass

# si elle existe, on supprime toutes les données

# on lit le csv
df_details = pd.read_csv('details_caves.csv', sep=";", encoding='latin1')
df_details.to_sql('caves', conn, if_exists='replace', index=False)
