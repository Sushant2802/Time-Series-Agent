# tools.py
# matplotlib.use('Agg')
import matplotlib
matplotlib.use('TkAgg')  # ✅ best for VS Code / local

from langchain.tools import tool
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os
import pandas as pd
from store import DataFrameStore, validate_column
from utils import print_ascii_line_plot

os.makedirs("plots", exist_ok=True)

# Stats Registry
STATS_OPERATIONS = {
    "mean": lambda s: float(s.mean()),
    "median": lambda s: float(s.median()),
    "std": lambda s: float(s.std()),
    "percentile": lambda s, p: float(np.percentile(s, p)) if p is not None else None,
}

@tool
def stats_tool(
    column: str,
    operation: str,
    start_date: str = None,
    end_date: str = None,
    percentile: float = None
):
    """
    Calculate statistics for a column.
    """

    df = DataFrameStore.get_df().copy()

    if df is None or df.empty:
        return "Error: No data available"

    try:
        column = validate_column(column)
    except Exception:
        return f"Error: Invalid column '{column}'"

    timestamp_col = df.columns[0]

    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        except:
            return "Error: Failed to parse timestamp column"

    if start_date:
        df = df[df[timestamp_col] >= pd.to_datetime(start_date)]

    if end_date:
        df = df[df[timestamp_col] <= pd.to_datetime(end_date)]

    if df.empty:
        return "Error: No data available after applying date filter"

    
    series = df[column].dropna()

    if series.empty:
        return "Error: No valid data in selected column"

    try:
        # ✅ SUMMARY
        if operation in ["summary", "describe", "all"]:
            return {
                "type": "summary",
                "column": column,
                "mean": round(series.mean(), 4),
                "median": round(series.median(), 4),
                "std": round(series.std(), 4),
                "min": round(series.min(), 4),
                "max": round(series.max(), 4)
            }

        # ✅ BELOW PERCENTILE
        if operation == "percentile_below":
            threshold = float(np.percentile(series, percentile))
            filtered = series[series <= threshold]

            return {
                "type": "percentile_below",
                "column": column,
                "percentile": percentile,
                "threshold": round(threshold, 4),
                "count": len(filtered)
            }

        # ✅ ABOVE PERCENTILE
        if operation == "percentile_above":
            threshold = float(np.percentile(series, percentile))
            filtered = series[series >= threshold]

            return {
                "type": "percentile_above",
                "column": column,
                "percentile": percentile,
                "threshold": round(threshold, 4),
                "count": len(filtered)
            }

        # ✅ RANGE
        if operation == "percentile_range":
            p_low, p_high = percentile

            low_val = float(np.percentile(series, p_low))
            high_val = float(np.percentile(series, p_high))

            filtered = series[(series >= low_val) & (series <= high_val)]

            return {
                "type": "percentile_range",
                "column": column,
                "low": p_low,
                "high": p_high,
                "low_threshold": round(low_val, 4),
                "high_threshold": round(high_val, 4),
                "count": len(filtered)
            }

        # ✅ NORMAL OPS
        if operation not in STATS_OPERATIONS:
            return "Error: Supported operations: mean, median, std, percentile, summary, percentile_range, percentile_below, percentile_above"

        if operation == "percentile":
            if percentile is None:
                return "Error: Percentile value required"
            value = STATS_OPERATIONS[operation](series, percentile)
        else:
            value = STATS_OPERATIONS[operation](series)

        return {
            "type": "single_stat",
            "column": column,
            "operation": operation,
            "value": round(float(value), 4)
        }

    except Exception as e:
        return f"Error calculating statistic: {str(e)}"

# # Plot Registry
PLOT_FUNCTIONS = {
    "line": lambda df, cols: [plt.plot(df.index, df[col], label=col) for col in cols],
    "bar":  lambda df, cols: [plt.bar(df.index[:150], df[col][:150], label=col, alpha=0.7) for col in cols],
    "hist": lambda df, cols: [plt.hist(df[col].dropna(), bins=25, alpha=0.7, label=col) for col in cols],
}


@tool

def plot_tool(

    columns: list[str],

    plot_type: str,

    start_date: str = None,

    end_date: str = None,

    filter_type: str = None,

    threshold: float = None,

    low_threshold: float = None,

    high_threshold: float = None,

    count: int = None

):
    """

    Generate visualization for selected columns with optional filtering.
    
    Supports line, bar, and histogram plots with date-range filtering.
    
    Filtering Rules:

    - Uses ACTUAL threshold values (from stats_tool), NOT percentiles

    - Supports:

        - percentile_below → uses `threshold`

        - percentile_above → uses `threshold`

        - percentile_range → uses `low_threshold` and `high_threshold`
    
    Chaining Contract:

    - Thresholds and count MUST come from stats_tool

    - NEVER recompute thresholds inside this tool

    - If count is provided → use it directly

    - Else → fallback to computed row count
    
    Args:

    - columns: list of column names

    - plot_type: {"line", "bar", "hist"}

    - start_date, end_date: optional date filters

    - filter_type: filtering mode

    - threshold: single cutoff value

    - low_threshold, high_threshold: range values

    - count: filtered count from stats_tool
    
    Returns:

    - Success message or error string

    """
 
 
    df = DataFrameStore.get_df().copy()
 
    if df is None or df.empty:

        return "Error: No data available"
 
    try:

        columns = [validate_column(col) for col in columns]

    except Exception:

        return f"Error: Invalid columns {columns}"
 
    timestamp_col = df.columns[0]
 
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):

        try:

            df[timestamp_col] = pd.to_datetime(df[timestamp_col])

        except:

            return "Error: Failed to parse timestamp column"
 
    if start_date:

        df = df[df[timestamp_col] >= pd.to_datetime(start_date)]
 
    if end_date:

        df = df[df[timestamp_col] <= pd.to_datetime(end_date)]
 
    if df.empty:

        return "Error: No data available after applying date filter"
 
    # ✅ APPLY FILTER USING ACTUAL THRESHOLD VALUES (NO RECOMPUTATION)

    col = columns[0]
 
    if filter_type == "percentile_below" and threshold is not None:

        df = df[df[col] <= threshold]
 
    elif filter_type == "percentile_above" and threshold is not None:

        df = df[df[col] >= threshold]
 
    elif filter_type == "percentile_range" and low_threshold is not None and high_threshold is not None:

        df = df[(df[col] >= low_threshold) & (df[col] <= high_threshold)]
 
    if df.empty:

        return "No data after applying filter"
 
    # ✅ USE COUNT FROM STATS TOOL (DO NOT RECOMPUTE)

    filtered_count = count if count is not None else len(df)
 
    if plot_type not in PLOT_FUNCTIONS:

        return "Error: Supported plot types: line, bar, hist"
 
    plot_id = str(uuid.uuid4())

    file_path = f"plots/{plot_id}.png"
 
    plt.figure(figsize=(10, 6))
 
    try:

        if plot_type == "line":

            df = df.set_index(timestamp_col)
 
        PLOT_FUNCTIONS[plot_type](df, columns)
 
        # ✅ DRAW ACTUAL THRESHOLD VALUES

        if threshold is not None:

            plt.axhline(threshold, linestyle="--", label=f"Threshold = {round(threshold, 4)}")
 
        if low_threshold is not None:

            plt.axhline(low_threshold, linestyle="--", label=f"Low = {round(low_threshold, 4)}")
 
        if high_threshold is not None:

            plt.axhline(high_threshold, linestyle="--", label=f"High = {round(high_threshold, 4)}")
 
        plt.title(f"{plot_type.capitalize()} Plot - {', '.join(columns)} (Count = {filtered_count})")

        plt.legend(title=f"Count = {filtered_count}")

        plt.grid(True, alpha=0.3)

        plt.tight_layout()
 
        plt.savefig(file_path)

        plt.show()

        plt.close()
 
        return f"Plot generated with filtering applied on {columns}"
 
    except Exception as e:

        plt.close()

        return f"Error generating plot: {str(e)}"
 

    

# # Stats Registry
# STATS_OPERATIONS = {
#     "mean": lambda s: float(s.mean()),
#     "median": lambda s: float(s.median()),
#     "std": lambda s: float(s.std()),
#     "percentile": lambda s, p: float(np.percentile(s, p)) if p is not None else None,
# }

# @tool
# def stats_tool(
#     column: str,
#     operation: str,
#     start_date: str = None,
#     end_date: str = None,
#     percentile: float = None
# ):
#     """
#     Calculate statistics for a column.

#     Use ONLY for numerical/statistical queries.

#     Args:
#     - column: column name
#     - operation: one of {"mean", "median", "std", "percentile", "summary"}
#     - start_date, end_date: optional date range
#     - percentile: required if operation = percentile

#     Returns:
#     - Result or error message
#     """

#     # Load data
#     df = DataFrameStore.get_df().copy()

#     if df is None or df.empty:
#         return "Error: No data available"

#     # Validate column
#     try:
#         column = validate_column(column)
#     except Exception:
#         return f"Error: Invalid column '{column}'"

#     # Detect timestamp column (assumes first column)
#     timestamp_col = df.columns[0]

#     # Ensure datetime
#     if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
#         try:
#             df[timestamp_col] = pd.to_datetime(df[timestamp_col])
#         except Exception:
#             return "Error: Failed to parse timestamp column"

#     # Apply date filtering
#     if start_date:
#         df = df[df[timestamp_col] >= pd.to_datetime(start_date)]

#     if end_date:
#         df = df[df[timestamp_col] <= pd.to_datetime(end_date)]

#     if df.empty:
#         return "Error: No data available after applying date filter"

#     # Extract series
#     series = df[column].dropna()

#     if series.empty:
#         return "Error: No valid data in selected column"

#     try:
#         # ✅ NEW: summary support (ONLY addition)
#         if operation in ["summary", "describe", "all"]:
#             return (
#                 f"Summary Statistics for {column}:\n"
#                 f"- Mean: {round(series.mean(), 4)}\n"
#                 f"- Median: {round(series.median(), 4)}\n"
#                 f"- Std: {round(series.std(), 4)}\n"
#                 f"- Min: {round(series.min(), 4)}\n"
#                 f"- Max: {round(series.max(), 4)}"
#             )

#         # Existing validation (slightly extended)
#         if operation not in STATS_OPERATIONS:
#             return "Error: Supported operations: mean, median, std, percentile, summary"

#         # Existing logic (UNCHANGED)
#         if operation == "percentile":
#             if percentile is None:
#                 return "Error: Percentile value (0-100) is required"
#             value = STATS_OPERATIONS[operation](series, percentile)
#         else:
#             value = STATS_OPERATIONS[operation](series)

#         value = round(float(value), 4)

#         return f"{operation.upper()} of {column} = {value} (from {start_date or 'start'} to {end_date or 'end'})"

#     except Exception as e:
#         return f"Error calculating statistic: {str(e)}"



# @tool
# def stats_tool(
#     column: str,
#     operation: str,
#     start_date: str = None,
#     end_date: str = None,
#     percentile: float = None
# ):
#     """
#     Calculate statistics for a column.

#     Use ONLY for numerical/statistical queries.

#     Args:
#     - column: column name
#     - operation: one of {"mean", "median", "std", "percentile"}
#     - start_date, end_date: optional date range
#     - percentile: required if operation = percentile

#     Returns:
#     - Result or error message
#     """

#     # Load data
#     df = DataFrameStore.get_df().copy()

#     if df is None or df.empty:
#         return "Error: No data available"

#     # Validate column
#     try:
#         column = validate_column(column)
#     except Exception:
#         return f"Error: Invalid column '{column}'"

#     # Detect timestamp column (assumes first column)
#     timestamp_col = df.columns[0]

#     # Ensure datetime
#     if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
#         try:
#             df[timestamp_col] = pd.to_datetime(df[timestamp_col])
#         except Exception:
#             return "Error: Failed to parse timestamp column"

#     # Apply date filtering
#     if start_date:
#         df = df[df[timestamp_col] >= pd.to_datetime(start_date)]

#     if end_date:
#         df = df[df[timestamp_col] <= pd.to_datetime(end_date)]

#     if df.empty:
#         return "Error: No data available after applying date filter"

#     # Extract series
#     series = df[column].dropna()

#     if series.empty:
#         return "Error: No valid data in selected column"

#     # Validate operation
#     if operation not in STATS_OPERATIONS:
#         return "Error: Supported operations: mean, median, std, percentile"

#     try:
#         # Compute
#         if operation == "percentile":
#             if percentile is None:
#                 return "Error: Percentile value (0-100) is required"
#             value = STATS_OPERATIONS[operation](series, percentile)
#         else:
#             value = STATS_OPERATIONS[operation](series)

#         value = round(float(value), 4)

#         return f"{operation.upper()} of {column} = {value} (from {start_date or 'start'} to {end_date or 'end'})"

#     except Exception as e:
#         return f"Error calculating statistic: {str(e)}"



# # Plot Registry
# PLOT_FUNCTIONS = {
#     "line": lambda df, cols: [plt.plot(df.index, df[col], label=col) for col in cols],
#     "bar":  lambda df, cols: [plt.bar(df.index[:150], df[col][:150], label=col, alpha=0.7) for col in cols],
#     "hist": lambda df, cols: [plt.hist(df[col].dropna(), bins=25, alpha=0.7, label=col) for col in cols],
# }


# @tool
# def plot_tool(
#     columns: list[str],
#     plot_type: str,
#     start_date: str = None,
#     end_date: str = None
# ):
#     """
#     Generate plot for given columns.

#     Use ONLY when user explicitly requests visualization.

#     Args:
#     - columns: list of column names
#     - plot_type: one of {"line", "bar", "hist"}
#     - start_date, end_date: optional date range

#     Returns:
#     - Success message or error
#     """

#     # Load data
#     df = DataFrameStore.get_df().copy()

#     if df is None or df.empty:
#         return "Error: No data available"

#     # Validate columns
#     try:
#         columns = [validate_column(col) for col in columns]
#     except Exception:
#         return f"Error: Invalid columns {columns}"

#     # Detect timestamp column (assumes first column)
#     timestamp_col = df.columns[0]

#     # Ensure datetime
#     if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
#         try:
#             df[timestamp_col] = pd.to_datetime(df[timestamp_col])
#         except Exception:
#             return "Error: Failed to parse timestamp column"

#     # Apply date filtering
#     if start_date:
#         df = df[df[timestamp_col] >= pd.to_datetime(start_date)]

#     if end_date:
#         df = df[df[timestamp_col] <= pd.to_datetime(end_date)]

#     if df.empty:
#         return "Error: No data available after applying date filter"

#     # Validate plot type
#     if plot_type not in PLOT_FUNCTIONS:
#         return "Error: Supported plot types: line, bar, hist"

#     # Generate plot
#     plot_id = str(uuid.uuid4())
#     file_path = f"plots/{plot_id}.png"

#     plt.figure(figsize=(10, 6))

#     try:
#         # Set index for time-series
#         if plot_type == "line":
#             df = df.set_index(timestamp_col)

#         # Call your existing plot functions
#         PLOT_FUNCTIONS[plot_type](df, columns)

#         plt.title(f"{plot_type.capitalize()} Plot - {', '.join(columns)}")
#         plt.legend()
#         plt.grid(True, alpha=0.3)
#         plt.tight_layout()

#         # ✅ Save + Show
#         plt.savefig(file_path)
#         plt.show()
#         plt.close()

#         return f"Successfully generated {plot_type} plot for {columns} between {start_date} and {end_date}"

#     except Exception as e:
#         plt.close()
#         return f"Error generating plot: {str(e)}"


@tool
def info_tool():
    """
    Get dataset information.

    Use for understanding dataset structure.

    Returns:
    - Summary of dataset or error
    """

    # Load data
    df = DataFrameStore.get_df()

    if df is None or df.empty:
        return "Error: No data available"

    try:
        columns = list(df.columns)
        dtypes = df.dtypes.astype(str).to_dict()
        row_count = len(df)

        # Format sample nicely
        sample = df.head(5).to_dict(orient="records")

        return (
            f"Dataset Info:\n"
            f"- Rows: {row_count}\n"
            f"- Columns: {columns}\n"
            f"- Data Types: {dtypes}\n"
            f"- Sample (first 5 rows): {sample}"
        )

    except Exception as e:
        return f"Error retrieving dataset info: {str(e)}"


# @tool
# def info_tool() -> dict:
#     """Get dataset information."""
#     df = DataFrameStore.get_df()
#     return {
#         "columns": list(df.columns),
#         "dtypes": df.dtypes.astype(str).to_dict(),
#         "sample": df.head(5).to_dict(orient="records"),
#         "row_count": len(df)
#     }



@tool
def filter_tool(
    column: str,
    operator: str,
    value: float
):
    """
    Filter dataset based on condition.

    Use for row-level filtering queries.

    Args:
    - column: column name
    - operator: one of {">", "<", ">=", "<=", "=="}
    - value: numeric value to compare

    Returns:
    - Filter result summary or error
    """

    # Load data
    df = DataFrameStore.get_df()

    if df is None or df.empty:
        return "Error: No data available"

    # Validate column
    try:
        column = validate_column(column)
    except Exception:
        return f"Error: Invalid column '{column}'"

    # Define operators
    ops = {
        ">":  lambda x: x > value,
        "<":  lambda x: x < value,
        ">=": lambda x: x >= value,
        "<=": lambda x: x <= value,
        "==": lambda x: x == value,
    }

    if operator not in ops:
        return "Error: Supported operators: >, <, >=, <=, =="

    try:
        filtered = df[ops[operator](df[column])]

        if filtered.empty:
            return f"No rows match condition: {column} {operator} {value}"

        return (
            f"Filter applied: {column} {operator} {value}\n"
            f"Rows remaining: {len(filtered)} out of {len(df)}"
        )

    except Exception as e:
        return f"Error applying filter: {str(e)}"



# @tool
# def filter_tool(column: str, operator: str, value: float) -> dict:
#     """Filter data."""
#     df = DataFrameStore.get_df()
#     column = validate_column(column)

#     ops = {
#         ">":  lambda x: x > value,
#         "<":  lambda x: x < value,
#         ">=": lambda x: x >= value,
#         "<=": lambda x: x <= value,
#         "==": lambda x: x == value,
#     }

#     if operator not in ops:
#         return {"error": f"Unsupported operator '{operator}'. Use: >, <, >=, <=, =="}

#     filtered = df[ops[operator](df[column])]
#     return {
#         "filtered_rows": len(filtered),
#         "message": f"Filtered to {len(filtered)} rows"
#     }


TOOLS = [info_tool, stats_tool, plot_tool, filter_tool]