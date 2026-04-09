# tools.py
# matplotlib.use('Agg')
# import matplotlib
# matplotlib.use('TkAgg')  # ✅ best for VS Code / local

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

import numpy as np
import pandas as pd
import uuid
import os

import webbrowser   # for auto-open
from store import DataFrameStore, validate_column
from IPython.display import display, Image   # Important for notebook display

import plotly.graph_objects as go
import plotly.express as px

from langchain.tools import tool
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os
import pandas as pd
from store import DataFrameStore, validate_column
from utils import print_ascii_line_plot
from typing import Union, List

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
    percentile: Union[float, List[float]] = None
):
    """
Compute statistics for a column in time-series data.

Supports: mean, median, std, percentile, summary,
percentile_below, percentile_above, percentile_range.

Args:
    column (str): Column name.
    operation (str): Type of statistic.
    start_date (str, optional): Filter start date.
    end_date (str, optional): Filter end date.
    percentile (float | list[float], optional):
        - single value → percentile / below / above
        - [low, high] → percentile_range

Returns:
    dict: Result with value/threshold(s) and count
    str: Error message if invalid input or no data
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
    
    # ✅ Percentile validation
    if operation in ["percentile", "percentile_below", "percentile_above"] and percentile is None:
        return "Error: Percentile value required"

    if operation == "percentile_range":
        if not isinstance(percentile, (list, tuple)) or len(percentile) != 2:
            return "Error: percentile_range requires percentile=[low, high]"

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
            if not isinstance(percentile, (list, tuple)) or len(percentile) != 2:
                return "Error: percentile_range requires percentile=[low, high]"

            p_low, p_high = sorted(percentile)

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
        # if operation == "percentile_range":
        #     p_low, p_high = percentile

        #     low_val = float(np.percentile(series, p_low))
        #     high_val = float(np.percentile(series, p_high))

        #     filtered = series[(series >= low_val) & (series <= high_val)]

        #     return {
        #         "type": "percentile_range",
        #         "column": column,
        #         "low": p_low,
        #         "high": p_high,
        #         "low_threshold": round(low_val, 4),
        #         "high_threshold": round(high_val, 4),
        #         "count": len(filtered)
        #     }

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
    Supports line, bar, and histogram plots with date-range filtering, data range filtering.
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
 
    if plot_type not in ["line", "bar", "hist"]:
        return "Error: Supported plot types: line, bar, hist"
 
    plot_id = str(uuid.uuid4())
    file_path = f"plots/{plot_id}.html"   # ← Now saves as interactive HTML (no GUI)
 
    try:
        # Prepare dataframe for plotting (exact same logic as before)
        df_plot = df.copy()

        if plot_type == "line":
            df_plot = df_plot.set_index(timestamp_col)
            fig = px.line(
                df_plot,
                y=columns,
                title=f"{plot_type.capitalize()} Plot - {', '.join(columns)} (Count = {filtered_count})"
            )
        elif plot_type == "bar":
            # Keep original 150-row limit for bar plots
            if len(df_plot) > 150:
                df_plot = df_plot.iloc[:150]
            fig = px.bar(
                df_plot,
                x=df_plot.index,
                y=columns,
                title=f"{plot_type.capitalize()} Plot - {', '.join(columns)} (Count = {filtered_count})"
            )
        elif plot_type == "hist":
            # Multi-column histogram with overlay (matches original matplotlib behavior)
            fig = go.Figure()
            for col_name in columns:
                fig.add_trace(
                    go.Histogram(
                        x=df_plot[col_name],
                        name=col_name,
                        opacity=0.7
                    )
                )
            fig.update_layout(barmode="overlay")

        # ✅ DRAW ACTUAL THRESHOLD VALUES (Plotly hlines)
        if threshold is not None:
            fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Threshold = {round(threshold, 4)}",
                annotation_position="top right"
            )
        if low_threshold is not None:
            fig.add_hline(
                y=low_threshold,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Low = {round(low_threshold, 4)}",
                annotation_position="top right"
            )
        if high_threshold is not None:
            fig.add_hline(
                y=high_threshold,
                line_dash="dash",
                line_color="blue",
                annotation_text=f"High = {round(high_threshold, 4)}",
                annotation_position="top right"
            )

        # Final layout (grid + legend with count)
        fig.update_layout(
            legend_title_text=f"Count = {filtered_count}",
            xaxis_title="Time" if plot_type == "line" else "Index",
            yaxis_title="Value",
            template="plotly_white",
            showlegend=True
        )

        fig.write_html(file_path)
        fig.show()  # Display the interactive plot in the notebook

        return f"Plot generated with filtering applied on {columns}"

    except Exception as e:
        return f"Error generating plot: {str(e)}"














# @tool
# def plot_tool(
#     columns: list[str],
#     plot_type: str,
#     start_date: str = None,
#     end_date: str = None,
#     filter_type: str = None,
#     threshold: float = None,
#     low_threshold: float = None,
#     high_threshold: float = None,
#     count: int = None
# ):
#     """
#     Generate visualization for selected columns with optional filtering.
#     Supports line, bar, and histogram plots with date-range filtering.
#     Filtering Rules:
#     - Uses ACTUAL threshold values (from stats_tool), NOT percentiles

#     - Supports:
#         - percentile_below → uses `threshold`
#         - percentile_above → uses `threshold`
#         - percentile_range → uses `low_threshold` and `high_threshold`
    
#     Chaining Contract:
#     - Thresholds and count MUST come from stats_tool
#     - NEVER recompute thresholds inside this tool
#     - If count is provided → use it directly
#     - Else → fallback to computed row count
    
#     Args:
#     - columns: list of column names
#     - plot_type: {"line", "bar", "hist"}
#     - start_date, end_date: optional date filters
#     - filter_type: filtering mode
#     - threshold: single cutoff value
#     - low_threshold, high_threshold: range values
#     - count: filtered count from stats_tool
    
#     Returns:
#     - Success message or error string
#     """
 
#     df = DataFrameStore.get_df().copy()
 
#     if df is None or df.empty:
#         return "Error: No data available"
 
#     try:
#         columns = [validate_column(col) for col in columns]
#     except Exception:
#         return f"Error: Invalid columns {columns}"
 
#     timestamp_col = df.columns[0]
 
#     if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
#         try:
#             df[timestamp_col] = pd.to_datetime(df[timestamp_col])
#         except:
#             return "Error: Failed to parse timestamp column"
 
#     if start_date:
#         df = df[df[timestamp_col] >= pd.to_datetime(start_date)]
 
#     if end_date:
#         df = df[df[timestamp_col] <= pd.to_datetime(end_date)]
 
#     if df.empty:
#         return "Error: No data available after applying date filter"
 
#     # APPLY FILTER USING ACTUAL THRESHOLD VALUES (NO RECOMPUTATION)
#     col = columns[0]
 
#     if filter_type == "percentile_below" and threshold is not None:
#         df = df[df[col] <= threshold]
 
#     elif filter_type == "percentile_above" and threshold is not None:
#         df = df[df[col] >= threshold]
 
#     elif filter_type == "percentile_range" and low_threshold is not None and high_threshold is not None:
#         df = df[(df[col] >= low_threshold) & (df[col] <= high_threshold)]
 
#     if df.empty:
#         return "No data after applying filter"
 
#     # USE COUNT FROM STATS TOOL (DO NOT RECOMPUTE)
#     filtered_count = count if count is not None else len(df)
 
#     if plot_type not in ["line", "bar", "hist"]:
#         return "Error: Supported plot types: line, bar, hist"
 
#     plot_id = str(uuid.uuid4())
#     file_path = f"plots/{plot_id}.html"   # ← Now saves as interactive HTML (no GUI)
 
#     try:
#         # Prepare dataframe for plotting (exact same logic as before)
#         df_plot = df.copy()

#         if plot_type == "line":
#             df_plot = df_plot.set_index(timestamp_col)
#             fig = px.line(
#                 df_plot,
#                 y=columns,
#                 title=f"{plot_type.capitalize()} Plot - {', '.join(columns)} (Count = {filtered_count})"
#             )
#         elif plot_type == "bar":
#             # Keep original 150-row limit for bar plots
#             if len(df_plot) > 150:
#                 df_plot = df_plot.iloc[:150]
#             fig = px.bar(
#                 df_plot,
#                 x=df_plot.index,
#                 y=columns,
#                 title=f"{plot_type.capitalize()} Plot - {', '.join(columns)} (Count = {filtered_count})"
#             )
#         elif plot_type == "hist":
#             # Multi-column histogram with overlay (matches original matplotlib behavior)
#             fig = go.Figure()
#             for col_name in columns:
#                 fig.add_trace(
#                     go.Histogram(
#                         x=df_plot[col_name],
#                         name=col_name,
#                         opacity=0.7
#                     )
#                 )
#             fig.update_layout(barmode="overlay")

#         # DRAW ACTUAL THRESHOLD VALUES (Plotly hlines)
#         if threshold is not None:
#             fig.add_hline(
#                 y=threshold,
#                 line_dash="dash",
#                 line_color="red",
#                 annotation_text=f"Threshold = {round(threshold, 4)}",
#                 annotation_position="top right"
#             )
#         if low_threshold is not None:
#             fig.add_hline(
#                 y=low_threshold,
#                 line_dash="dash",
#                 line_color="green",
#                 annotation_text=f"Low = {round(low_threshold, 4)}",
#                 annotation_position="top right"
#             )
#         if high_threshold is not None:
#             fig.add_hline(
#                 y=high_threshold,
#                 line_dash="dash",
#                 line_color="blue",
#                 annotation_text=f"High = {round(high_threshold, 4)}",
#                 annotation_position="top right"
#             )

#         # Final layout (grid + legend with count)
#         fig.update_layout(
#             legend_title_text=f"Count = {filtered_count}",
#             xaxis_title="Time" if plot_type == "line" else "Index",
#             yaxis_title="Value",
#             template="plotly_white",
#             showlegend=True
#         )

#         fig.write_html(file_path)

#         return f"Plot generated with filtering applied on {columns}"

#     except Exception as e:
#         return f"Error generating plot: {str(e)}"







# @tool

# def plot_tool(

#     columns: list[str],

#     plot_type: str,

#     start_date: str = None,

#     end_date: str = None,

#     filter_type: str = None,

#     threshold: float = None,

#     low_threshold: float = None,

#     high_threshold: float = None,

#     count: int = None

# ):
#     """

#     Generate visualization for selected columns with optional filtering.
    
#     Supports line, bar, and histogram plots with date-range filtering.
    
#     Filtering Rules:

#     - Uses ACTUAL threshold values (from stats_tool), NOT percentiles

#     - Supports:

#         - percentile_below → uses `threshold`

#         - percentile_above → uses `threshold`

#         - percentile_range → uses `low_threshold` and `high_threshold`
    
#     Chaining Contract:

#     - Thresholds and count MUST come from stats_tool

#     - NEVER recompute thresholds inside this tool

#     - If count is provided → use it directly

#     - Else → fallback to computed row count
    
#     Args:

#     - columns: list of column names

#     - plot_type: {"line", "bar", "hist"}

#     - start_date, end_date: optional date filters

#     - filter_type: filtering mode

#     - threshold: single cutoff value

#     - low_threshold, high_threshold: range values

#     - count: filtered count from stats_tool
    
#     Returns:

#     - Success message or error string

#     """
 
 
#     df = DataFrameStore.get_df().copy()
 
#     if df is None or df.empty:

#         return "Error: No data available"
 
#     try:

#         columns = [validate_column(col) for col in columns]

#     except Exception:

#         return f"Error: Invalid columns {columns}"
 
#     timestamp_col = df.columns[0]
 
#     if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):

#         try:

#             df[timestamp_col] = pd.to_datetime(df[timestamp_col])

#         except:

#             return "Error: Failed to parse timestamp column"
 
#     if start_date:

#         df = df[df[timestamp_col] >= pd.to_datetime(start_date)]
 
#     if end_date:

#         df = df[df[timestamp_col] <= pd.to_datetime(end_date)]
 
#     if df.empty:

#         return "Error: No data available after applying date filter"
 
#     # ✅ APPLY FILTER USING ACTUAL THRESHOLD VALUES (NO RECOMPUTATION)

#     col = columns[0]
 
#     if filter_type == "percentile_below" and threshold is not None:

#         df = df[df[col] <= threshold]
 
#     elif filter_type == "percentile_above" and threshold is not None:

#         df = df[df[col] >= threshold]
 
#     elif filter_type == "percentile_range" and low_threshold is not None and high_threshold is not None:

#         df = df[(df[col] >= low_threshold) & (df[col] <= high_threshold)]
 
#     if df.empty:

#         return "No data after applying filter"
 
#     # ✅ USE COUNT FROM STATS TOOL (DO NOT RECOMPUTE)

#     filtered_count = count if count is not None else len(df)
 
#     if plot_type not in PLOT_FUNCTIONS:

#         return "Error: Supported plot types: line, bar, hist"
 
#     plot_id = str(uuid.uuid4())

#     file_path = f"plots/{plot_id}.png"
 
#     plt.figure(figsize=(10, 6))
 
#     try:

#         if plot_type == "line":

#             df = df.set_index(timestamp_col)
 
#         PLOT_FUNCTIONS[plot_type](df, columns)
 
#         # ✅ DRAW ACTUAL THRESHOLD VALUES

#         if threshold is not None:

#             plt.axhline(threshold, linestyle="--", label=f"Threshold = {round(threshold, 4)}")
 
#         if low_threshold is not None:

#             plt.axhline(low_threshold, linestyle="--", label=f"Low = {round(low_threshold, 4)}")
 
#         if high_threshold is not None:

#             plt.axhline(high_threshold, linestyle="--", label=f"High = {round(high_threshold, 4)}")
 
#         plt.title(f"{plot_type.capitalize()} Plot - {', '.join(columns)} (Count = {filtered_count})")

#         plt.legend(title=f"Count = {filtered_count}")

#         plt.grid(True, alpha=0.3)

#         plt.tight_layout()
 
#         plt.savefig(file_path)

#         plt.show()

#         plt.close()
 
#         return f"Plot generated with filtering applied on {columns}"
 
#     except Exception as e:

#         plt.close()

#         return f"Error generating plot: {str(e)}"
 


# @tool
# def plot_tool(
#     columns: list[str],
#     plot_type: str,
#     start_date: str = None,
#     end_date: str = None,
#     filter_type: str = None,
#     threshold: float = None,
#     low_threshold: float = None,
#     high_threshold: float = None,
#     count: int = None
# ):
#     """
#     Generate visualization using Plotly and save as PNG.
    
#     Displays the plot directly in Jupyter notebook (.ipynb).
    
#     Supports line, bar, and histogram plots with optional date-range and percentile filtering.
    
#     Filtering Rules:
#     - Uses ACTUAL threshold values from stats_tool (never recomputes)
#     - percentile_below → uses `threshold`
#     - percentile_above → uses `threshold`
#     - percentile_range → uses `low_threshold` + `high_threshold`
    
#     Chaining Contract:
#     - Thresholds and count MUST come from stats_tool
#     - start_date/end_date default to None (uses full dataset if not provided)
    
#     Args:
#         columns: List of column names to plot
#         plot_type: Type of plot ("line", "bar", "hist")
#         start_date: Optional start date (None = full data)
#         end_date: Optional end date (None = full data)
#         filter_type: Filter mode ("percentile_below", "percentile_above", "percentile_range")
#         threshold: Single threshold value
#         low_threshold: Lower bound for range filter
#         high_threshold: Upper bound for range filter
#         count: Filtered data count from stats_tool (preferred over recomputing)
    
#     Returns:
#         Success message with plot details or error string
#     """
 
#     df = DataFrameStore.get_df().copy()
 
#     if df is None or df.empty:
#         return "Error: No data available"
 
#     try:
#         columns = [validate_column(col) for col in columns]
#     except Exception:
#         return f"Error: Invalid columns {columns}"
 
#     timestamp_col = df.columns[0]
 
#     if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
#         try:
#             df[timestamp_col] = pd.to_datetime(df[timestamp_col])
#         except:
#             return "Error: Failed to parse timestamp column"
 
#     if start_date:
#         df = df[df[timestamp_col] >= pd.to_datetime(start_date)]
#     if end_date:
#         df = df[df[timestamp_col] <= pd.to_datetime(end_date)]
 
#     if df.empty:
#         return "Error: No data available after applying date filter"
 
#     # Apply filter
#     col = columns[0]
#     if filter_type == "percentile_below" and threshold is not None:
#         df = df[df[col] <= threshold]
#     elif filter_type == "percentile_above" and threshold is not None:
#         df = df[df[col] >= threshold]
#     elif filter_type == "percentile_range" and low_threshold is not None and high_threshold is not None:
#         df = df[(df[col] >= low_threshold) & (df[col] <= high_threshold)]
 
#     if df.empty:
#         return "No data after applying filter"
 
#     filtered_count = count if count is not None else len(df)
 
#     if plot_type not in ["line", "bar", "hist"]:
#         return "Error: Supported plot types: line, bar, hist"
 
#     plot_id = str(uuid.uuid4())
#     file_path = f"plots/{plot_id}.png"   # ← Now always PNG
 
#     try:
#         df_plot = df.copy()

#         # Create figure
#         if plot_type == "line":
#             df_plot = df_plot.set_index(timestamp_col)
#             fig = px.line(df_plot, y=columns,
#                           title=f"Line Plot - {', '.join(columns)} (Count = {filtered_count})")
#         elif plot_type == "bar":
#             if len(df_plot) > 150:
#                 df_plot = df_plot.iloc[:150]
#             fig = px.bar(df_plot.reset_index(), 
#                          x=timestamp_col if timestamp_col in df_plot.columns else "index",
#                          y=columns,
#                          title=f"Bar Plot - {', '.join(columns)} (Count = {filtered_count})")
#         else:  # hist
#             fig = go.Figure()
#             for c in columns:
#                 fig.add_trace(go.Histogram(x=df_plot[c].dropna(), name=c, opacity=0.7, nbinsx=30))
#             fig.update_layout(barmode="overlay")

#         # Add threshold lines
#         if threshold is not None:
#             fig.add_hline(y=threshold, line_dash="dash", line_color="red",
#                           annotation_text=f"Threshold = {round(threshold, 4)}")
#         if low_threshold is not None:
#             fig.add_hline(y=low_threshold, line_dash="dash", line_color="green",
#                           annotation_text=f"Low = {round(low_threshold, 4)}")
#         if high_threshold is not None:
#             fig.add_hline(y=high_threshold, line_dash="dash", line_color="blue",
#                           annotation_text=f"High = {round(high_threshold, 4)}")

#         fig.update_layout(
#             legend_title_text=f"Count = {filtered_count}",
#             xaxis_title="Time" if plot_type == "line" else "Index",
#             yaxis_title="Value",
#             template="plotly_white",
#             height=620,
#             width=920
#         )

#         # Save as PNG
#         fig.write_image(file_path)

#         # Display the image directly in the notebook
#         display(Image(filename=file_path))

#         return f"{plot_type.capitalize()} plot generated successfully for column(s): {columns}\nSaved as: {file_path}"

#     except Exception as e:
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



TOOLS = [info_tool, stats_tool, plot_tool, filter_tool]