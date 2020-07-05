import os
import glob
import sqlite3

import pandas as pd


df = (
    pd.concat(
        pd.read_csv(
            fi, header=None, names=['name', 'gender', 'count']
        ).assign(year=int(os.path.basename(fi)[3:7]))
        for fi in glob.glob('data/yob*.txt')
    ).pivot_table(
        'count', ['name', 'year'], 'gender'
    ).fillna(0).astype(int).reset_index().rename(
        columns={'M': 'male', 'F': 'female', 'year': 'year', 'name': 'name'}
    )
)
df.columns.name = ''
df['count'] = df['female'] + df['male']
df['cumulative_count'] = (
    df.reset_index().groupby(['name', 'year'])
    .sum().groupby(level=0)['count'].cumsum()
    .reset_index()['count']
)
df['percent_male'] = df['male'] / df['count']

df_max = df.groupby('name')['count'].max().rename('max')
print(df_max.max())

df_total = df.groupby('year')['count'].sum().rename('total').to_frame()
df_total['cumulative_total'] = df_total.cumsum()

df = df.set_index(['name', 'year'])

with sqlite3.connect('../data/newborns.db') as con:
    df.to_sql('newborns_name_year_gender', con)
    df_max.to_sql('newborns_name_max', con)
    df_total.to_sql('newborns_total', con)

    cursor = con.cursor()
    queries = ' '.join([
        'CREATE INDEX name_index ON newborns_name_year_gender (name, year);'
        'CREATE INDEX name ON newborns_name_max (name);'
        'CREATE INDEX year ON newborns_total (year);'
    ])
    cursor.executescript(queries)
