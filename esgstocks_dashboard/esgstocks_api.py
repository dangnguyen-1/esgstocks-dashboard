"""
Filename: esgstocks_api.py
Author: Dang Nguyen
Description: A module for defining the ESGStockAPI class, which reads, processes, and analyzes
             ESG and stock price datasets for S&P 500 companies. It includes methods to classify
             ESG and business risk levels, build breakdowns for Sankey diagrams, extract
             stock price trends, and analyze ESG scores with stock returns. The class serves as
             the backend for the interactive dashboard.
"""

import pandas as pd

class ESGStockAPI:
    def __init__(self):
        """
        Parameters: none
        Returns: none
        Does: initializes an ESGStockAPI object with empty ESG and stock DataFrames
        """
        self.esg = None
        self.stocks = None

    def read_data(self, esg_filename, stocks_filename):
        """
        Parameters: esg_filename (str) - the file path to the ESG dataset in CSV format
                    stocks_filename (str) - the file path to the stocks dataset in CSV format
        Returns: none
        Does: reads and processes the ESG and stock datasets from the specified CSV files
              into their respective DataFrames
        """
        # Read the ESG dataset into a DataFrame and convert the "totalEsg" column to numeric values
        self.esg = pd.read_csv(esg_filename)
        self.esg["totalEsg"] = pd.to_numeric(self.esg["totalEsg"])

        # Create a dictionary mapping ticker symbols to company names
        ticker_to_name = dict(zip(self.esg["Symbol"], self.esg["Full Name"]))

        # Read the stock dataset into a DataFrame and convert the "Date" column
        # to datetime without timezone
        initial_stocks_df = pd.read_csv(stocks_filename)
        initial_stocks_df["Date"] = pd.to_datetime(initial_stocks_df["Date"]).dt.tz_localize(None)

        # Reshape the DataFrame from wide to long format and keep only rows
        # that match companies in the ESG DataFrame
        adjusted_stocks_df = initial_stocks_df.melt(id_vars = ["Date"],
                                                    var_name = "Symbol", value_name = "Price")
        adjusted_stocks_df = adjusted_stocks_df[adjusted_stocks_df["Symbol"].isin(ticker_to_name)]
        adjusted_stocks_df["Full Name"] = adjusted_stocks_df["Symbol"].map(ticker_to_name)

        self.stocks = adjusted_stocks_df

    def get_company_names(self):
        """
        Parameters: none
        Returns: a list
        Does: extracts a sorted list of company names from the ESG DataFrame
        """
        return sorted(self.esg["Full Name"].tolist())

    @staticmethod
    def classify_esg(esg_score):
        """
        Parameters: esg_score (float) - the overall esg score of the company
        Returns: a string
        Does: classifies the overall ESG score into high, medium, or low levels.
        """
        if esg_score > 30:
            return "High ESG"
        elif esg_score >= 20:
            return "Medium ESG"
        return "Low ESG"

    @staticmethod
    def classify_biz_risk(biz_risk):
        """
        Parameters: biz_risk (int) - the overall business risk score of the company
        Returns: a string
        Does: classifies the overall business risk score into high, medium, or low levels.
        """
        if biz_risk <= 3:
            return "Low Business Risk"
        elif biz_risk <= 6:
            return "Medium Business Risk"
        return "High Business Risk"

    def build_esg_risk_hierarchy(self, company_names, esg_levels = None, biz_risks = None):
        """
        Parameters: company_names (list) - a list of company names to include
                    esg_levels (list, optional) – the esg levels to filter by
                    biz_risks (list, optional) – the business risk levels to filter by
        Returns: a DataFrame
        Does: generates a DataFrame with each selected company's individual ESG dimension scores,
              ESG level, and business risk levels
        """
        # Filter the ESG DataFrame to include only the selected companies
        fltr_esg_df = self.esg[self.esg["Full Name"].isin(company_names)].copy()

        # Classify the ESG and business risk levels and filter the DataFrame
        # based on the selected levels if specified
        fltr_esg_df["ESG Level"] = fltr_esg_df["totalEsg"].apply(self.classify_esg)
        if esg_levels:
            fltr_esg_df = fltr_esg_df[fltr_esg_df["ESG Level"].isin(esg_levels)]

        fltr_esg_df["Business Risk Level"] = fltr_esg_df["overallRisk"].apply(self.classify_biz_risk)
        if biz_risks:
            fltr_esg_df = fltr_esg_df[fltr_esg_df["Business Risk Level"].isin(biz_risks)]

        # Iterate over the DataFrame and for each company, append the individual score
        # of each ESG dimension, along with its corresponding ESG and business risk levels,
        # to the designated list
        esg_risk_breakdown = []
        for _, row in fltr_esg_df.iterrows():
            for dim, col in zip(["Environmental", "Social", "Governance"],
                                ["environmentScore", "socialScore", "governanceScore"]):
                esg_risk_breakdown.append({"Company": row["Full Name"],
                                           "ESG Dimension": dim, "ESG Level": row["ESG Level"],
                                           "Business Risk Level": row["Business Risk Level"],
                                           "Score": row[col]})

        return pd.DataFrame(esg_risk_breakdown)

    def extract_stock_price_trends(self, company_names, start_date = None, end_date = None):
        """
        Parameters: company_names (list) - a list of company names to include
                    start_date (datetime.date, optional) - the earliest date to filter
                                                           the stock prices by
                    end_date (datetime.date, optional) - the latest date to filter
                                                         the stock prices by
        Returns: a DataFrame
        Does: generates a DataFrame with the date, company name, and stock price for each record,
              filtered by the selected companies and date range
        """
        # Filter the stock DataFrame to include only the selected companies
        fltr_stocks_df = self.stocks[self.stocks["Full Name"].isin(company_names)].copy()

        # Apply optional start and end date filters to the stock prices
        if start_date:
            fltr_stocks_df = fltr_stocks_df[fltr_stocks_df["Date"] >= pd.to_datetime(start_date)]
        if end_date:
            fltr_stocks_df = fltr_stocks_df[fltr_stocks_df["Date"] <= pd.to_datetime(end_date)]

        return fltr_stocks_df[["Date", "Full Name", "Price"]].sort_values(["Full Name", "Date"])

    def analyze_esg_vs_stock_returns(self, company_names, start_date, end_date, biz_risks = None):
        """
        Parameters: company_names (list) - a list of company names to include
                    start_date (datetime.date, optional) - the earliest date to filter
                                                           the stock prices by
                    end_date (datetime.date, optional) - the latest date to filter
                                                         the stock prices by
                    biz_risks (list, optional) – the business risk levels to filter by
        Returns: a DataFrame
        Does: computes the stock return percentages over the selected date range and
              generates a DataFrame with each selected company's overall ESG score, stock return,
              and business risk level
        """
        # Filter the ESG DataFrame to include only the selected companies
        fltr_esg_df = self.esg[self.esg["Full Name"].isin(company_names)].copy()

        # Classify the business risk levels and filter the DataFrame
        # based on the selected levels if specified
        fltr_esg_df["Business Risk Level"] = fltr_esg_df["overallRisk"].apply(self.classify_biz_risk)
        if biz_risks:
            fltr_esg_df = fltr_esg_df[fltr_esg_df["Business Risk Level"].isin(biz_risks)]

        # Compute the stock returns in percentage over the selected date range
        stock_prices_df = self.extract_stock_price_trends(fltr_esg_df["Full Name"].tolist(),
                                                          start_date, end_date)
        grouped_prices = stock_prices_df.groupby("Full Name")
        stock_returns_df = grouped_prices.agg(start_price = ("Price", "first"),
                                              end_price = ("Price", "last"))
        stock_returns_df["Stock Return"] = ((stock_returns_df["end_price"] -
                                             stock_returns_df["start_price"]) /
                                            stock_returns_df["start_price"] * 100)
        stock_returns_df.reset_index(inplace = True)

        # Merge the ESG DataFrame with the stock returns DataFrame
        merged_df = pd.merge(fltr_esg_df, stock_returns_df, on = "Full Name", how = "inner")

        return merged_df[["Full Name", "totalEsg", "Stock Return", "Business Risk Level"]]