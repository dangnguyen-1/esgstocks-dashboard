"""
Filename: esgstocks_explore.py
Author: Dang Nguyen
Description: A module for building an interactive ESG and stock performance dashboard using
             HoloViz Panel. It connects user interface widgets to data processing and
             plotting functions, enabling users to filter S&P 500 companies and visualize
             ESG-risk flows, stock price trends, and ESG score vs. stock return relationships.
             The layout includes tabs for an overview, a Sankey diagram, a line plot, and
             a scatter plot, which are all dynamically rendered based on user selections.
"""

import panel as pn
import sankey as sk
import plot as pt
from esgstocks_api import ESGStockAPI

# Loads javascript dependencies and configures Panel (required)
pn.extension()

# Initialize API, read and process the ESG and stock datasets from the specified CSV files
# into their respective DataFrames
api = ESGStockAPI()
api.read_data("data/sp500_esg_data.csv", "data/sp500_price_data.csv")

# SEARCH WIDGET DECLARATIONS (FOR FILTERING DATA)
company_selector = pn.widgets.MultiChoice(name = "Select Companies",
                                          options = api.get_company_names(),
                                          value = [api.get_company_names()[1]],
                                          solid = False, sizing_mode = "stretch_width")
biz_risk_filter = pn.widgets.CheckButtonGroup(name = "Business Risk Level",
                                              options = ["Low Business Risk", "Medium Business Risk",
                                                         "High Business Risk"], button_type = "danger",
                                              orientation = "vertical", value = [])
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
def get_sankey_diagram(company_names, esg_levels, biz_risks, width, height):
    """
    Parameters: company_names (list) - a list of company names to include
                esg_levels (list) – the esg levels to filter by
                biz_risks (list) – the business risk levels to filter by
                width (int) – the width of the Sankey diagram
                height (int) – the height of the Sankey diagram
    Returns: a Plotly Sankey diagram
    Does: filters the ESG DataFrame by selected companies, ESG levels, and business risk levels,
          and creates a Sankey diagram visualizing the flow from ESG dimensions to risk levels,
          sized based on the given width and height
    """
    df = api.build_esg_risk_hierarchy(company_names, esg_levels = esg_levels, biz_risks = biz_risks)
    if df.empty:
        return pn.pane.Markdown("### No visualization is available for the selected filters.")
    fig = sk.make_sankey(df, "Company", "ESG Dimension", "ESG Level", "Business Risk Level",
                         vals = "Score", title = "ESG Dimension to Business Risk Flow "
                                                 "for Selected S&P 500 Companies (2023–2024)",
                         width = width, height = height)
    return fig

def get_line_plot(company_names, date_range, width, height):
    """
    Parameters: company_names (list) - a list of company names to include
                date_range (tuple) - the start date and end date to filter by
                width (int) – the width of the Sankey diagram
                height (int) – the height of the Sankey diagram
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

def get_scatter_plot(company_names, date_range, biz_risks, width, height):
    """
    Parameters: company_names (list) - a list of company names to include
                date_range (tuple) - the start date and end date to filter by
                biz_risks (list) – the business risk levels to filter by
                width (int) – the width of the Sankey diagram
                height (int) – the height of the Sankey diagram
    Returns: a Plotly scatter plot
    Does: computes stock returns for the selected companies over the specified date range,
          and creates a scatter plot comparing ESG scores with stock returns, colored by
          business risk level and sized based on the given width and height
    """
    start_date, end_date = date_range
    df = api.analyze_esg_vs_stock_returns(company_names, start_date = start_date, end_date = end_date,
                                          biz_risks = biz_risks)
    if df.empty:
        return pn.pane.Markdown("### No visualization is available for the selected filters.")

    fig = pt.make_scatter_plot(df, x_col = "totalEsg", y_col = "Stock Return",
                               title = "ESG Score vs. Stock Return for Selected S&P 500 Companies",
                               label = {"totalEsg": "ESG Score", "Stock Return": "Stock Return (%)"},
                               color = "Business Risk Level", width = width, height = height)
    return fig

# CALLBACK BINDINGS
sankey_diagram = pn.bind(get_sankey_diagram, company_selector, esg_filter, biz_risk_filter,
                         width_slider, height_slider)
line_plot = pn.bind(get_line_plot, company_selector, date_range_slider,
                    width_slider, height_slider)
scatter_plot = pn.bind(get_scatter_plot, company_selector, date_range_slider, biz_risk_filter,
                       width_slider, height_slider)

# DASHBOARD WIDGET CONTAINERS
card_width = 320
search_card = pn.Card(pn.Column(company_selector, esg_filter, biz_risk_filter),
                      title = "Search Filters", width = card_width, collapsed = False)
plot_card = pn.Card(pn.Column(date_range_slider, width_slider, height_slider),
                    title = "Plot Settings", width = card_width, collapsed = False)

# OVERVIEW INFO
overview = pn.pane.Markdown("""
# Welcome to the S&P 500 ESG and Stock Performance Dashboard
This dashboard provides insights into the relationship between S&P 500 companies’ ESG 
(Environmental, Social, and Governance) scores and their financial performance from 2023 to 2024, 
using two datasets: one containing ESG ratings and another tracking historical stock prices.

## 1. ESG Dimension to Business Risk Flow  
Explore how companies are distributed across ESG dimensions and business risk levels 
through a Sankey Diagram.  
**Widgets available**: Company Selector, ESG Level Filter, Business Risk Filter, Width Slider, 
Height Slider

<br>

## 2. Stock Price Trends Over Time  
Visualize stock price movements over a selected time range for the chosen companies 
through a line plot.  
**Widgets available**: Company Selector, Date Range Slider, Width Slider, Height Slider

<br>

## 3. ESG Score vs. Stock Return  
Analyze how ESG scores correlate with stock performance within a specified time frame 
for the chosen companies through a scatter plot.  
**Widgets available**: Company Selector, Business Risk Filter, Date Range Slider, 
Width Slider, Height Slider
""", sizing_mode = "stretch_width", margin = (10, 25))

# LAYOUT
layout = pn.template.FastListTemplate(
    title = "S&P 500 ESG and Stock Performance Dashboard",
    sidebar = [search_card, plot_card],
    theme_toggle = False,
    main = [
        pn.Tabs(
            ("Overview", overview),
            ("ESG to Risk Flow", sankey_diagram),
            ("Stock Price Trends", line_plot),
            ("ESG Score vs. Stock Return", scatter_plot),
            active = 0
        )
    ],
    header_background = "#a93226"

).servable()

layout.show()