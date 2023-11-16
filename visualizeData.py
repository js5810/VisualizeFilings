import requests
import os
from dotenv import load_dotenv
import pandas as pd
import json
import plotly.graph_objects as go
from typing import List    # for annotating function parameter types
import finnhub

class VisualizeFilings:

  def __init__(self):
    """
    Constructor, makes headers and dictionaries used by other methods    
    """
    self.ticker_to_CIK = {}
    load_dotenv()  # to load env variables from .env file for API key
    self.sec_header = {
      "User-Agent": os.getenv("USER_AGENT")
    }
    self.finnhub_header = {
      "X-Finnhub-Token": os.getenv("FINNHUB_API_KEY")
    }

    with open("./company_tickers.json") as f:
      company_list = json.load(f)["data"]

    for company in company_list:
      # each company is structured as (CIK, Name, Ticker, Exchange)
      ticker = company[2]
      CIK = company[0]
      self.ticker_to_CIK[ticker] = CIK

    return


  def getMetricDF(self, ticker: str, metric: str) -> pd.DataFrame:
    """ Returns dataframe containing the ticker's time series data for the metric
    :param p1: ticker of company
    :param p2: metric to get
    :return: dataframe containing data for that company's metric
    """
    CIK = self.ticker_to_CIK[ticker]
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(CIK).zfill(10)}.json"
    company_facts = requests.get(url, headers=self.sec_header).json()
    try:
      UNITS = list(company_facts["facts"]["us-gaap"][metric]["units"])[0]   # simply use first units
      metric_df = pd.DataFrame(company_facts["facts"]["us-gaap"][metric]["units"][UNITS])
      metric_df = metric_df[metric_df.frame.notna()][metric_df.form == "10-Q"]  # retain only valid time frames
      return metric_df, UNITS
    except:
      print(f"{ticker} has no {metric}")
      return None
  

  def getSimilarCompanies(self, ticker: str, criteria: str) -> List[str]:
    """ Returns a list of companies similar to the given ticker
    :param p1: ticker of company
    :param p2: criteria for finding similar companies, one of (sector, industry, subIndustry)
    :return: list containing similar companies
    """
    url = f"https://finnhub.io/api/v1/stock/peers?symbol={ticker}&grouping={criteria}"
    similar_companies_json = requests.get(url, headers=self.finnhub_header).json()
    return list(similar_companies_json)


  def lineGraph(self, metric: str, tickers: List[str]) -> None:
    """ Generates one line for each company for easy comparison over time 
    :param p1: the metric to be plotted (such as EPS)
    :param p2: list of company tickers to be compared (if only one the program selects around 10 similar companies in the same sector)
    """
    if len(tickers) == 1:
      tickers = self.getSimilarCompanies(tickers[0], "sector")
    fig = go.Figure()
    for ticker in tickers:
      try:
        metric_df, UNITS = self.getMetricDF(ticker, metric)
        fig.add_trace(go.Scatter(x=metric_df["end"], y=metric_df["val"],
                                  mode="lines",
                                  name=ticker))
      except:
        continue
    fig.update_layout(title=f"{metric} Over Time",
                      title_x=0.5,
                      xaxis_title="Time",
                      yaxis_title=f"{metric} ({UNITS})",
                      legend_title="Tickers")
    fig.show()
    return
   

  def areaGraph(self, metric: str, tickers: List[str]) -> None:
    """ Generates one layer for each company for easy comparison over time 
    :param p1: the metric to be plotted (such as EPS)
    :param p2: list of company tickers to be compared (if only one the program selects around 10 similar companies in the same sector)
    """
    if len(tickers) == 1:
      tickers = self.getSimilarCompanies(tickers[0], "sector")
    fig = go.Figure()
    for ticker in tickers:
      try:
        metric_df, UNITS = self.getMetricDF(ticker, metric)
        fig.add_trace(go.Scatter(
          x=metric_df["end"], y=metric_df["val"],
          hoverinfo="x+y",
          mode="lines",
          line=dict(width=0.5),
          stackgroup="one",
          name=ticker
        ))
      except:
        continue
    fig.update_layout(title=f"{metric} Over Time",
                      title_x=0.5,
                      xaxis_title="Time",
                      yaxis_title=f"{metric} ({UNITS})",
                      legend_title="Tickers")
    fig.show()
    return
  

  def pieChart(self, metric: str, tickers: List[str]) -> None:
    """ Compare the most recently reported meric for companies
    :param p1: the metric to be compared
    :param p2: list of company tickers to be compared (if only one the program selects around 10 similar companies in the same sector)
    """
    if len(tickers) == 1:
      tickers = self.getSimilarCompanies(tickers[0], "sector")
    val_list = []
    for ticker in tickers:
      try:
        metric_df, UNITS = self.getMetricDF(ticker, metric)
        val_list.append(metric_df.tail(1)["val"].iloc[0])
      except:
        continue
    fig = go.Figure(data=[go.Pie(labels=tickers, values=val_list)])
    fig.update_layout(title=f"{metric} Comparison",
                      title_x=0.5,
                      legend_title="Tickers")
    fig.show()
    return


vis = VisualizeFilings()
#vis.areaGraph("EarningsPerShareBasic", ["TSLA", "AAPL", "T"])
#vis.lineGraph("EarningsPerShareBasic", ["TSLA", "AAPL", "T"])
vis.pieChart("EarningsPerShareBasic", ["TSLA"])
