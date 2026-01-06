"""
Filename: esgstocks_api.py
Author: Dang Nguyen
Description: A module for defining the ESGStockAPI class, which reads, processes, and analyzes
             ESG and stock price datasets for S&P 500 companies. It includes methods to classify
             ESG and beta levels, build breakdowns for Sankey diagrams, extract
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
    def classify_esg(percentile):
        """
        Parameters: percentile (float) - the value representing the company’s ESG performance
                                         relative to other companies
        Returns: a string
        Does: classifies the company's overall ESG score into high, medium, or low levels
              based on its percentile
        """
        if percentile >= 66:
            return "High ESG"
        elif percentile >= 33:
            return "Medium ESG"
        return "Low ESG"


    @staticmethod
    def classify_beta(beta):
        """
        Parameters: beta (float) - stock beta (market risk sensitivity)
        Returns: a string
        Does: classifies beta into low, medium, or high market risk levels
        """
        if beta < 0.8:
            return "Low Beta"
        elif beta <= 1.2:
            return "Medium Beta"
        return "High Beta"


    def build_esg_risk_hierarchy(self, company_names, esg_levels = None, beta_levels = None):
        """
        Parameters: company_names (list) - a list of company names to include
                    esg_levels (list, optional) – the esg levels to filter by
                    beta_levels (list, optional) – the beta levels to filter by
        Returns: a DataFrame
        Does: generates a DataFrame with each selected company's individual ESG dimension scores,
              ESG level, and beta levels
        """
        # Filter the ESG DataFrame to include only the selected companies
        fltr_esg_df = self.esg[self.esg["Full Name"].isin(company_names)].copy()

        # Classify the ESG and beta levels and filter the DataFrame
        # based on the selected levels if specified
        fltr_esg_df["ESG Level"] = fltr_esg_df["percentile"].apply(self.classify_esg)
        if esg_levels:
            fltr_esg_df = fltr_esg_df[fltr_esg_df["ESG Level"].isin(esg_levels)]

        fltr_esg_df["Beta Level"] = fltr_esg_df["beta"].apply(self.classify_beta)
        if beta_levels:
            fltr_esg_df = fltr_esg_df[fltr_esg_df["Beta Level"].isin(beta_levels)]

        # Iterate over the DataFrame and for each company, append the individual score
        # of each ESG dimension, along with its corresponding ESG and beta levels,
        # to the designated list
        esg_risk_breakdown = []
        for _, row in fltr_esg_df.iterrows():
            for dim, col in zip(["Environmental", "Social", "Governance"],
                                ["environmentScore", "socialScore", "governanceScore"]):
                esg_risk_breakdown.append({"Company": row["Full Name"],
                                           "ESG Dimension": dim, "ESG Level": row["ESG Level"],
                                           "Beta Level": row["Beta Level"],
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


    def compute_rolling_returns(self, company_names, end_date, months = 6):
        """
        Parameters: company_names (list) - a list of company names to include
                    end_date (datetime.date) - the end date for the rolling return window
                    months (int, optional) - the lookback window length in months
        Returns: a DataFrame
        Does: computes the stock return percentages over a fixed lookback window ending at the selected date
              and generates a DataFrame with each selected company’s start price, end price, and rolling stock return
        """
        end_dt = pd.to_datetime(end_date)
        start_dt = end_dt - pd.DateOffset(months = months)

        # Compute the stock returns in percentage over the selected lookback window
        prices_df = self.extract_stock_price_trends(company_names, start_date = start_dt,
                                                    end_date = end_dt)
        if prices_df.empty:
            return pd.DataFrame(columns = ["Full Name", "start_price", "end_price", "Stock Return"])

        grouped = prices_df.sort_values(["Full Name", "Date"]).groupby("Full Name", as_index = False)
        start_end = grouped.agg(start_price = ("Price", "first"), end_price = ("Price", "last"))
        start_end["Stock Return"] = ((start_end["end_price"] - start_end["start_price"]) /
                                     start_end["start_price"] * 100)

        return start_end


    def analyze_esg_vs_stock_returns(self, company_names, end_date, beta_levels = None, months = 6):
        """
        Parameters: company_names (list) - a list of company names to include
                    end_date (datetime.date) - the end date for computing rolling stock returns
                    beta_levels (list, optional) – the beta levels to filter by
                    months (int, optional) – the length of the rolling return window in months
        Returns: a DataFrame
        Does: computes the rolling stock returns in percentage ending on the specified date and
              generates a DataFrame with each selected company's overall ESG score,
              rolling stock return, and beta level
        """
        # Filter the ESG DataFrame to include only the selected companies
        fltr_esg_df = self.esg[self.esg["Full Name"].isin(company_names)].copy()

        # Classify the beta levels and filter the DataFrame
        # based on the selected levels if specified
        fltr_esg_df["Beta Level"] = fltr_esg_df["beta"].apply(self.classify_beta)
        if beta_levels:
            fltr_esg_df = fltr_esg_df[fltr_esg_df["Beta Level"].isin(beta_levels)]

        # Compute the rolling stock returns in percentage ending on the specified date
        stock_returns_df = self.compute_rolling_returns(fltr_esg_df["Full Name"].tolist(),
                                                        end_date = end_date, months = months)

        # Merge the ESG DataFrame with the stock returns DataFrame
        merged_df = pd.merge(fltr_esg_df, stock_returns_df, on = "Full Name", how = "inner")

        return merged_df[["Full Name", "totalEsg", "Stock Return", "Beta Level"]]