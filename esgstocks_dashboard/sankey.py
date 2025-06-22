"""
Filename: sankey.py
Author: Dang Nguyen
Description: A library for generating customizable multi-level Sankey diagrams using Plotly.
             This module provides helper functions to transform categorical data into
             source-target-value relationships and maps categorical labels to integer codes
             suitable for Sankey diagram visualization.
"""

import plotly.graph_objects as go
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def stack_columns(df, cols):
    """
    Parameters: df (pd.DataFrame) - a DataFrame with categorical columns used to form
                                    source-target relationships
                cols (list) - a list of column names of the DataFrame
    Returns: a Dataframe
    Does: pairs adjacent columns of the given DataFrame to form source-target relationships and
          stacks them vertically to create a new DataFrame with source, target, and value columns
    """
    # Create an empty list to store DataFrames for each column pair
    stacked_dfs = []

    # Iterate and create a DataFrame for each adjacent column pair with source, target, and
    # value columns, then add it to the list
    for col1, col2 in zip(cols, cols[1:]):
        pair_df = df[[col1, col2, "value"]]
        pair_df.columns = ["src", "targ", "value"]
        stacked_dfs.append(pair_df)

    # Concatenate all DataFrames in the list into a single DataFrame
    stacked_df = pd.concat(stacked_dfs, ignore_index = True)

    return stacked_df

def code_mapping(df, src, targ):
    """
    Parameters: df (pd.DataFrame) - a DataFrame with a source column and a target column
                src (str) - the name of the source column
                targ (str) - the name of the target column
    Returns: a tuple
    Does: maps and replaces labels in the source and target columns of the DataFrame
          with integer codes
    """
    # Create a list of unique labels from both the source and target columns and
    # a list of integer codes for each label
    labels = list(set(df[src]).union(set(df[targ])))
    codes = list(range(len(labels)))

    # Create a mapping from the labels to the integer codes
    lc_map = dict(zip(labels, codes))

    # Replace the values in the source and target columns in the DataFrame with the integer codes
    df[src] = df[src].map(lc_map)
    df[targ] = df[targ].map(lc_map)

    return df, labels

def make_sankey(df, *cols, vals = None, title = None, **kwargs):
    """
    Parameters: df (pd.DataFrame) - a DataFrame with columns to be visualized as levels
                                    in the Sankey diagram
                *cols (tuple) - two or more columns used as source and target nodes
                                in the Sankey diagram
                vals (str, optional) - the name of the column with link thicknesses
                                       between the source and target nodes
                title (str, optional) - the title of the Sankey diagram
                **kwargs (dict, optional) - keyword arguments to customize the Sankey diagram
    Returns: a Plotly Sankey diagram
    Does: creates a Sankey diagram from the given DataFrame
    """
    # Check if there are at least two columns form source-target pairs
    assert len(cols) >= 2, "You need at least two columns to create a Sankey diagram."

    # Use specified value column or assign a uniform link thickness of 1
    if vals:
        df["value"] = df[vals]
    else:
        df["value"] = 1

    # Restructure the given DataFrame to a source-target-value format
    df = stack_columns(df, cols)

    # Map and replace labels in the source and target columns of the DataFrame with integer codes
    df, labels = code_mapping(df, "src", "targ")

    # Assign a color to each node
    cmap = cm.get_cmap("tab20", len(labels))
    node_colors = []
    for i in range(len(labels)):
        rgba = cmap(i)
        hex_color = mcolors.to_hex(rgba)
        node_colors.append(hex_color)

    # Assign a matching color to each link based on its source node with lower opacity
    link_colors = []
    for src in df["src"]:
        r, g, b = mcolors.to_rgb(node_colors[src])
        rgba_str = f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, 0.3)"
        link_colors.append(rgba_str)

    # Customize layout, sizing, and fonts of the Sankey diagram
    padding = kwargs.get("padding", 50)
    thickness = kwargs.get("thickness", 25)

    width = kwargs.get("width", 800)
    height = kwargs.get("height", 600)

    title_font = kwargs.get("title_font", {"size": 24, "family": "Times New Roman",
                                           "color": "black"})
    font_family = kwargs.get("font_family", "Times News Roman")
    font_color = kwargs.get("font_color", "black")
    font_size = kwargs.get("font_size", 13)

    # Define the Sankey diagram structure
    link = {"source": df["src"], "target": df["targ"], "value": df["value"], "color": link_colors}
    node = {"label": labels, "pad": padding, "thickness": thickness, "color": node_colors}

    # Create the Sankey diagram
    sk = go.Sankey(link = link, node = node)
    fig = go.Figure(sk)
    fig.update_layout(autosize = False, width = width, height = height,
                      title = {"text": title, "font": title_font, "x": 0.5, "xanchor": "center"},
                      font_family = font_family, font_color = font_color, font_size = font_size)

    return fig