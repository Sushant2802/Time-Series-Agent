# store.py
import pandas as pd
from config import DATA_PATH
from difflib import get_close_matches

class DataFrameStore:
    _df = None

    @classmethod
    def load(cls):
        cls._df = pd.read_csv(DATA_PATH)
        print(f"✅ Loaded {len(cls._df)} rows and {len(cls._df.columns)} columns")
        # Convert first column to datetime if possible (common in time series)
        if not pd.api.types.is_datetime64_any_dtype(cls._df.iloc[:, 0]):
            try:
                cls._df.iloc[:, 0] = pd.to_datetime(cls._df.iloc[:, 0])
            except:
                pass

    @classmethod
    def get_df(cls):
        if cls._df is None:
            raise ValueError("Data not loaded. Call DataFrameStore.load() first.")
        return cls._df

    @classmethod
    def columns(cls):
        return list(cls.get_df().columns)



def validate_column(column: str) -> str:
    df_cols = DataFrameStore.columns()

    # Exact match
    if column in df_cols:
        return column

    # Case-insensitive match
    for col in df_cols:
        if col.lower() == column.lower():
            return col

    # Fuzzy match
    matches = get_close_matches(column, df_cols, n=1, cutoff=0.6)
    if matches:
        return matches[0]

    raise ValueError(f"Column '{column}' not found. Available columns: {df_cols}")