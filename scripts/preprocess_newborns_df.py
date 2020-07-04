import os
import glob
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
        columns={'M': 'Male', 'F': 'Female', 'year': 'Year', 'name': 'Name'}
    )
)
df['Count'] = df['Female'] + df['Male']
df['Cumulative Count'] = (
    df.reset_index().groupby(['Name', 'Year'])
    .sum().groupby(level=0)['Count'].cumsum()
    .reset_index()['Count']
)
df = df.set_index('Year')
df['Percent Male'] = df['Male'] / df['Count']
df_total = df.groupby('Year')['Count'].sum().rename('Total').to_frame()
df_total['Cumulative Total'] = df_total.cumsum()
df = df.join(df_total)
df['Percent Total'] = df['Count'] / df['Total']
df['Percent Cumulative'] = df['Cumulative Count'] / df['Cumulative Total']
df.to_pickle('../data/newborns.1880.2018.pkl')
