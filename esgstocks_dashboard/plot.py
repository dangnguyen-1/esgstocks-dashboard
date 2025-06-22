"""
Filename: plot.py
Author: Dang Nguyen
Description: A library for generating customizable line plots and scatter plots using Plotly.
"""

import plotly.express as px

def make_line_plot(df, x_col, y_col, title = None, label = None, color = None, **kwargs):
    """
    Parameters: df (pd.DataFrame) - a DataFrame to be visualized as a line plot
                x_col (str) - the name of the column to be used on the x-axis
                y_col (str) - the name of the column to be used on the y-axis
                title (str, optional) - the title of the line plot
                label (dict, optional) - custom labels for axes and legends
                color (str, optional) - the name of the column to be used for color grouping
                **kwargs (dict, optional) - keyword arguments to customize the scatter plot
    Returns: a Plotly line plot
    Does: creates a line plot from the given DataFrame
    """
    # Create the base line plot
    fig = px.line(df, x = x_col, y = y_col, title = title, labels = label, color = color)

    # Customize sizing and fonts of the line plot
    width = kwargs.get("width", 1100)
    height = kwargs.get("height", 600)

    title_font = kwargs.get("title_font", {"size": 24, "family": "Times New Roman",
                                           "color": "black"})
    font_family = kwargs.get("font_family", "Times News Roman")
    font_color = kwargs.get("font_color", "black")
    font_size = kwargs.get("font_size", 14)

    fig.update_layout(autosize = False, width = width, height = height,
                      title = {"font": title_font, "x": 0.5, "xanchor": "center"},
                      font_family = font_family, font_color = font_color, font_size = font_size)

    return fig

def make_scatter_plot(df, x_col, y_col, title = None, label = None, color = None, **kwargs):
    """
    Parameters: df (pd.DataFrame) - a DataFrame to be visualized as a scatter plot
                x_col (str) - the name of the column to be used on the x-axis
                y_col (str) - the name of the column to be used on the y-axis
                title (str, optional) - the title of the scatter plot
                label (dict, optional) - custom labels for axes and legends
                color (str, optional) - the name of the column to be used for color grouping
                **kwargs (dict, optional) - keyword arguments to customize the scatter plot
    Returns: a Plotly scatter plot
    Does: creates a scatter plot from the given DataFrame
    """
    # Create the base scatter plot
    fig = px.scatter(df, x = x_col, y = y_col, title = title, labels = label, color = color,
                     hover_name = "Full Name")

    # Customize sizing and fonts of the scatter plot
    width = kwargs.get("width", 1100)
    height = kwargs.get("height", 600)

    title_font = kwargs.get("title_font", {"size": 24, "family": "Times New Roman",
                                           "color": "black"})
    font_family = kwargs.get("font_family", "Times New Roman")
    font_color = kwargs.get("font_color", "black")
    font_size = kwargs.get("font_size", 14)

    fig.update_layout(autosize = False, width = width, height = height,
                      title = {"font": title_font, "x": 0.5, "xanchor": "center"},
                      font_family = font_family, font_color = font_color, font_size = font_size)

    return fig