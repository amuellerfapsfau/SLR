import pandas as pd
from sqlalchemy import create_engine

def store_dicts_in_sqlite_with_pandas(db_name, table_name, list_of_dicts):
    # Convert the list of dicts into a DataFrame
    df = pd.DataFrame(list_of_dicts)
    
    # Create a SQLAlchemy engine
    engine = create_engine(f'sqlite:///{db_name}')
    
    # Store the DataFrame in the SQLite database
    df.to_sql(table_name, engine, if_exists='replace', index=False)