"""
Filename: esgstocks_explore.py
Author: Dang Nguyen
Description: A module for building an interactive ESG and stock performance dashboard using
             HoloViz Panel. It connects user interface widgets to data processing and
             plotting functions, enabling users to filter S&P 500 companies and visualize
             ESG-beta flows, stock price trends, and ESG score vs. stock return associations.
             The layout includes tabs for an overview, a Sankey diagram, a line plot, and
             a scatter plot, which are all dynamically rendered based on user selections.
"""

import panel as pn
from src import sankey as sk
from src import plot as pt
from src.esgstocks_api import ESGStockAPI
from pathlib import Path

# Loads javascript dependencies and configures Panel (required)
pn.extension()

# Initialize API, read and process the ESG and stock datasets from the specified CSV files
# into their respective DataFrames
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

api = ESGStockAPI()
api.read_data(DATA_DIR / "sp500_esg_data.csv", DATA_DIR / "sp500_price_data.csv")


# SEARCH WIDGET DECLARATIONS (FOR FILTERING DATA)
company_selector = pn.widgets.MultiChoice(name = "Select Companies",
                                          options = api.get_company_names(),
                                          value = [api.get_company_names()[1]],
                                          solid = False, sizing_mode = "stretch_width")
beta_filter = pn.widgets.CheckButtonGroup(name = "Beta Level", options = ["Low Beta", "Medium Beta", "High Beta"],
                                          button_type = "danger", value = [])
esg_filter = pn.widgets.CheckButtonGroup(name = "ESG Level",
                                         options = ["Low ESG", "Medium ESG", "High ESG"],
                                         button_type = "success", value = [])


# PLOTTING WIDGET DECLARATIONS
date_range_slider = pn.widgets.DateRangeSlider(name = "Date Range",
                                               start = api.stocks["Date"].min(),
                                               end = api.stocks["Date"].max(),
                                               value = (api.stocks["Date"].min(),
                                                        api.stocks["Date"].max()),
                                               sizing_mode = "stretch_width")
width_slider = pn.widgets.IntSlider(name = "Width", start = 200, end = 2000, step = 100,
                                    value = 1000)
height_slider = pn.widgets.IntSlider(name = "Height", start = 200, end = 2500, step = 100,
                                     value = 700)


# CALLBACK FUNCTIONS
def get_sankey_diagram(company_names, esg_levels, beta_levels, width, height):
    """
    Parameters: company_names (list) - a list of company names to include
                esg_levels (list) – the esg levels to filter by
                beta_levels (list) – the beta levels to filter by
                width (int) – the width of the Sankey diagram
                height (int) – the height of the Sankey diagram
    Returns: a Plotly Sankey diagram
    Does: filters the ESG DataFrame by selected companies, ESG levels, and beta levels,
          and creates a Sankey diagram visualizing the flow from ESG dimensions to beta levels,
          sized based on the given width and height
    """
    df = api.build_esg_risk_hierarchy(company_names, esg_levels = esg_levels, beta_levels = beta_levels)
    if df.empty:
        return pn.pane.Markdown("### No visualization is available for the selected filters.")

    fig = sk.make_sankey(df, "Company", "ESG Dimension", "ESG Level", "Beta Level",
                         vals = "Score", title = "ESG Dimension to Beta Level Flow for "
                                                 "Selected S&P 500 Companies (2023)",
                         width = width, height = height)

    return fig


def get_line_plot(company_names, date_range, width, height):
    """
    Parameters: company_names (list) - a list of company names to include
                date_range (tuple) - the start date and end date to filter by
                width (int) – the width of the line plot
                height (int) – the height of the line plot
    Returns: a Plotly line plot
    Does: filters the stock Dataframe for the selected companies and date range, and
          creates a line plot visualizing stock price trends over time, sized based on
          the given width and height
    """
    start_date, end_date = date_range

    df = api.extract_stock_price_trends(company_names, start_date = start_date, end_date = end_date)
    if df.empty:
        return pn.pane.Markdown("### No visualization is available for the selected filters.")

    fig = pt.make_line_plot(df, x_col = "Date", y_col = "Price",
                            title = "Stock Price Trends Over Time for Selected S&P 500 Companies",
                            label = {"Full Name": "Companies", "Price": "Stock Price (USD)"},
                            color = "Full Name", width = width, height = height)

    return fig


def get_scatter_plot(company_names, date_range, beta_levels, width, height):
    """
    Parameters: company_names (list) - a list of company names to include
                date_range (tuple) - the start date and end date to filter by
                beta_levels (list) – the beta levels to filter by
                width (int) – the width of the scatter plot
                height (int) – the height of the scatter plot
    Returns: a Plotly scatter plot
    Does: computes rolling stock returns for the selected companies ending on the specified date,
          and creates a scatter plot comparing ESG scores with rolling stock returns, colored by
          beta levels and sized based on the given width and height
    """
    _, end_date = date_range

    df = api.analyze_esg_vs_stock_returns(company_names, end_date = end_date,
                                          beta_levels = beta_levels, months = 6)
    if df.empty:
        return pn.pane.Markdown("### No visualization is available for the selected filters.")

    fig = pt.make_scatter_plot(df, x_col = "totalEsg", y_col = "Stock Return",
                               title = "ESG Score vs. Rolling 6-Month Stock Return for Selected S&P 500 Companies",
                               label = {"totalEsg": "ESG Score", "Stock Return": "Stock Return (%)"},
                               color = "Beta Level", width = width, height = height)

    return fig


# CALLBACK BINDINGS
sankey_diagram = pn.bind(get_sankey_diagram, company_selector, esg_filter, beta_filter,
                         width_slider, height_slider)
line_plot = pn.bind(get_line_plot, company_selector, date_range_slider,
                    width_slider, height_slider)
scatter_plot = pn.bind(get_scatter_plot, company_selector, date_range_slider, beta_filter,
                       width_slider, height_slider)


# DASHBOARD WIDGET CONTAINERS
card_width = 320
search_card = pn.Card(pn.Column(company_selector, esg_filter, beta_filter),
                      title = "Search Filters", width = card_width, collapsed = False)
plot_card = pn.Card(pn.Column(date_range_slider, width_slider, height_slider),
                    title = "Plot Settings", width = card_width, collapsed = False)


# OVERVIEW INFO
overview = pn.pane.Markdown("""
# Welcome to the S&P 500 ESG and Stock Performance Dashboard
This dashboard provides insights into the relationship between S&P 500 companies’ ESG 
(Environmental, Social, and Governance) scores and their stock performance from 2023 to 2024, 
using two datasets: one containing ESG ratings in 2023 and another tracking historical stock prices
from 2023 to August 2024.

## 1. ESG Dimension to Beta Level Flow  
Explore how companies are distributed across ESG dimensions and beta levels (market risk)
through a Sankey Diagram.  
**Widgets available**: Company Selector, ESG Level Filter, Beta Level Filter, Width Slider, Height Slider

<br>

## 2. Stock Price Trends Over Time  
Visualize stock price movements over a selected time range for the chosen companies through a line plot.  
**Widgets available**: Company Selector, Date Range Slider, Width Slider, Height Slider

<br>

## 3. ESG Score vs. Rolling Stock Return  
Explore how ESG scores are associated with stock performance for the chosen companies through a scatter plot, 
colored by beta level. For this plot, returns are computed over a fixed 6-month window ending on 
the selected date (the Date Range Slider controls the return end date for this plot).  
**Widgets available**: Company Selector, Beta Level Filter, Date Range Slider, Width Slider, Height Slider

<br>

### Methodology Notes
- **ESG levels** are based on the dataset’s percentile rankings (relative performance within the dataset).
- **Beta levels** use standard cutoffs: Low (β < 0.8), Medium (0.8–1.2), High (β > 1.2).
- These visualizations show **associations**, not causal relationships.

""", sizing_mode = "stretch_width", margin = (10, 25))


# LAYOUT
layout = pn.template.FastListTemplate(
    title = "S&P 500 ESG and Stock Performance Dashboard",
    sidebar = [search_card, plot_card],
    theme_toggle = False,
    main = [
        pn.Tabs(
            ("Overview", overview),
            ("ESG to Beta Flow", sankey_diagram),
            ("Stock Price Trends", line_plot),
            ("ESG Score vs. Rolling Stock Return", scatter_plot),
            active = 0
        )
    ],
    header_background = "#a93226"

).servable()

layout.show()