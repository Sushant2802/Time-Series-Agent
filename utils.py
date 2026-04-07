# utils.py
import numpy as np

def print_ascii_line_plot(series, column_name: str, max_width: int = 75, max_height: int = 14):
    """Clean ASCII line plot optimized for VS Code terminal"""
    data = np.array(series.dropna().values)
    if len(data) == 0:
        print("No data to plot.")
        return
    if len(data) > max_width:
        indices = np.linspace(0, len(data)-1, max_width, dtype=int)
        data = data[indices]

    min_val, max_val = data.min(), data.max()
    if abs(max_val - min_val) < 1e-6:
        print(f"All values in {column_name} are approximately same: {min_val:.2f}")
        return

    print(f"\n📈 Line Plot → {column_name}")
    print(f"   Min: {min_val:.2f}   |   Max: {max_val:.2f}")
    print("─" * (max_width + 12))

    height = max_height
    for row in range(height, 0, -1):
        line = ""
        threshold = min_val + (row / height) * (max_val - min_val)
        for val in data:
            if val >= threshold:
                line += "█"
            elif val >= threshold - (max_val - min_val) / height * 0.5:
                line += "▓"
            elif val >= threshold - (max_val - min_val) / height * 1.0:
                line += "▒"
            else:
                line += " "
        print(f"│ {line}")

    print("└" + "─" * max_width)
    print("   " + "Start".ljust(max_width//2 - 2) + "End".rjust(max_width//2 + 2))
    print("      ↑ Time / Index →\n")