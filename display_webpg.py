#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 31 11:14:37 2020

@author: sawleen

# File must be run from Terminal
# To run, change working directory in Terminal first:
## "cd Documents/Leen/Python/stock_analysis"
# Next, key in "streamlit run display_webpg.py"
"""
import streamlit as st
import time
import math
import plotly.express as px
import pandas as pd
import numpy as np
#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
import os
os.chdir('/Users/sawleen/Documents/Leen/Python/stock_analysis')
import data.get_yf_data as get_yf_data
import data.get_sgi_data as get_sgi_data
#import data.get_morningstar_data as get_ms_data

#### Basics
st.title("STOCKS SUMMARY")

# Cache functions (to improve loading speed)
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_stocks_map():
    stocks_map = pd.read_csv('data/stocks_map.csv', index_col='Name')
    return stocks_map

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_all_sectors(stocks_map):
    stock_sectors = pd.read_csv('data/stock_sectors.csv', index_col=False)
    stock_sectors = stock_sectors['Sector'].tolist()
    return stock_sectors

def filter_stock_selection(stocks_map, stock_sector_selected):
    if stock_sector_selected == 'All':
        stocks_map_filtered = stocks_map
    else:
        stocks_map_filtered = stocks_map.loc[stocks_map['Sector'] == stock_sector_selected,stocks_map.columns]
    return stocks_map_filtered

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def fetch_yf_data(sgx_symbol):
    yf_data = get_yf_data.Data(sgx_symbol)
    return yf_data

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_stock_name(yf_data):
    stock_name = yf_data.get_name_disp()
    return stock_name

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_industry(yf_data):
    industry = yf_data.get_industry()
    return industry

# Fetch data
stocks_map = get_stocks_map()
stock_sectors = get_all_sectors(stocks_map)

# Display on page
st.sidebar.header("Filter by sector:")
stock_sector_selected = st.sidebar.radio("", stock_sectors)
stocks_map_filtered = filter_stock_selection(stocks_map, stock_sector_selected)

# Sector summary
st.sidebar.header('Show sector summary?')
show_sector_summary = st.sidebar.checkbox('Yes')
summary_df_columns = ['None','Name', 'Symbol', 'Market Cap (bil)', 'PB Ratio', 'PE Ratio','Dividend Payout Ratio','Income Growth (Avg YoY)', 'ROE', 'Dividend (fwd)', 'Strategy','Tally(%)', 'Tally', 'Price/Cash Flow', 'Debt/Equity', 'Interest Coverage']

#st.sidebar.header("Sort sector summary by:")
sort_summary = st.sidebar.selectbox('Sort sector summary by:', summary_df_columns)
# Filters for PB ratio and Dividend yield
#st.sidebar.header('Minimum dividend yield (%)')
min_cap = st.sidebar.slider('Minimum market cap (bil)', 0,10,0,1)
min_div = st.sidebar.slider('Minimum dividend yield (%)',min_value=0.0, max_value=10.0, value=0.0, step=0.5)
#st.sidebar.header('Maximum PB ratio')
max_pb = st.sidebar.slider('Maximum PB ratio',min_value=3.0, max_value=0.0, value=3.0, step=-0.1)
min_intcov = st.sidebar.slider('Minimum interest coverage', -10,10,-10,1)
max_dpr = st.sidebar.slider('Maximum dividend payout ratio',0,200,100,10)

# Select individual stock
all_stock_names = stocks_map_filtered.index.values
st.sidebar.header("Select stock:")
sgx_name = st.sidebar.selectbox("", all_stock_names)

#### Sector summary
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_sector_summary(sector, sort_summary):
    summary_df = pd.read_csv('data/sector_summaries/{}.csv'.format(sector))
    return summary_df

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_sector_average(summary_df):
    summary_avg={}
    for col in summary_df.columns:
        if col == 'Name':
            summary_avg[col] = 'Average'
        elif col == 'Symbol':
            summary_avg[col]=None
        elif col == 'Strategy':
            avg_strategy = summary_df[col].value_counts().sort_values(ascending=False).index[0]
            summary_avg[col] = avg_strategy
        elif col in ['Tally(%)','Tally']:
            filter_summary = summary_df.loc[summary_df['Strategy']==avg_strategy, [col]] # Filter only rows that correspond to average strategy
            summary_avg[col]=(filter_summary[col].sum(skipna=True))/(filter_summary[col].notna().sum())
        else:
            summary_avg[col]=(summary_df[col].sum(skipna=True))/(summary_df[col].notna().sum()) # Find average while excluding NA values

    summary_avg_df = pd.DataFrame.from_dict(summary_avg,orient='index').T
    return summary_avg_df


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def filter_sector_summary(summary_df, min_cap, min_div, max_pb, min_intcov, max_dpr, sort_summary):
    # Filter min dividend / PB ratio
    summary_df = summary_df.loc[summary_df['Market Cap (bil)']>=min_cap]
    summary_df = summary_df.loc[summary_df['Dividend (fwd)']>=min_div]
    summary_df = summary_df.loc[summary_df['PB Ratio']<=max_pb]
    summary_df = summary_df.loc[summary_df['Interest Coverage']>=min_intcov]
    summary_df1 = summary_df.loc[summary_df['Dividend Payout Ratio']<=max_dpr]
    summary_df2 = summary_df.loc[np.isnan(summary_df['Dividend Payout Ratio'])]
    summary_df = pd.concat([summary_df1,summary_df2])
    # Sort summary
    ascending_order = {'Name':True,
                       'Symbol':True,
                       'Market Cap (bil)':False,
                       'PB Ratio':True,
                       'PE Ratio':True,
                       'Dividend Payout Ratio':True,
                       'Income Growth (Avg YoY)':False,
                       'ROE':False,
                       'Dividend (fwd)':False,
                       'Strategy':True,
                       'Tally(%)':False,
                       'Tally':False,
                       'Price/Cash Flow': True,
                       'Debt/Equity':True,
                       'Interest Coverage':False}
    if sort_summary != 'None':
        summary_df = summary_df.sort_values(sort_summary, ascending=ascending_order[sort_summary])
    return summary_df

if show_sector_summary:
    # Sector summary
    st.subheader('Sector summary (Stocks)')
    summary_df = get_sector_summary(stock_sector_selected, sort_summary)
    # Filter sector summary
    summary_df_filtered = filter_sector_summary(summary_df, min_cap, min_div, max_pb, min_intcov, max_dpr, sort_summary)
    # Display sector summary and average
    summary_df_style_format = {'Market Cap (bil)':'{:.2f}',
                              'PB Ratio':'{:.1f}',
                              'PE Ratio':'{:.1f}',
                              'Dividend Payout Ratio':'{:.0f}',
                              'Income Growth (Avg YoY)':'{:.1f}',
                              'ROE':'{:.1f}',
                              'Dividend (fwd)':'{:.2f}',
                              'Tally(%)':'{:.0f}',
                              'Tally':'{:.0f}',
                              'Price/Cash Flow':'{:.2f}',
                              'Debt/Equity':'{:.2f}',
                              'Interest Coverage':'{:.2f}'}
    st.dataframe(summary_df_filtered.style.format(summary_df_style_format))
    # Summary of sector average
    st.subheader('Sector summary (Average)')
    summary_avg_df = get_sector_average(summary_df)
    st.dataframe(summary_avg_df.style.format(summary_df_style_format))


# Fetch data
sgx_symbol = stocks_map.at[sgx_name, 'SGX_Symbol']
yf_data = fetch_yf_data(sgx_symbol)
stock_name = get_stock_name(yf_data)
sector = stocks_map.at[sgx_name, 'Sector']

# Display on page
st.title("{} ({})".format(stock_name, sgx_symbol)) # Page title
st.markdown('Sector: {}'.format(sector)) # Sector
industry = get_industry(yf_data)
st.markdown('Industry: {}'.format(industry))

#### Financial ratios
# Cache functions
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_stats_df(yf_data):
    stats_df = yf_data.get_basic_stats()
    return stats_df

# Fetch data
stats_df = get_stats_df(yf_data)

# Display on page
st.subheader('Basic stats')
st.dataframe(stats_df.style.format("{:.2f}")) # Display table (rounded to 2 dp)

#### 3 year average growth
# Cache functions
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_inc_3yr_avg_growth_df(yf_data):
    [inc_yoy_avg_growth_df, inc_yrly_growth_df] = yf_data.process_inc_statement()
    return [inc_yoy_avg_growth_df, inc_yrly_growth_df]

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_string_pos(inc_yoy_avg_growth_df):
    positivity=0
    for col in range(len(inc_yoy_avg_growth_df.columns)):
        if inc_yoy_avg_growth_df.iat[0,col]==None:
            return None
        elif inc_yoy_avg_growth_df.iat[0,col]>0:
            positivity+=1
    if positivity == 2:
        string_pos = ': POSITIVE'
    elif positivity ==0:
        string_pos = ': NEGATIVE'
    else:
        string_pos = ''
    return string_pos

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def adjust_inc_growth_df(inc_yoy_avg_growth_df):
    inc_yoy_avg_growth_df_adjusted = inc_yoy_avg_growth_df.copy()
    for col in range(len(inc_yoy_avg_growth_df_adjusted.columns)):
        inc_yoy_avg_growth_df_adjusted.iloc[0,col]='{}%'.format(inc_yoy_avg_growth_df_adjusted.iloc[0,col])
    return inc_yoy_avg_growth_df_adjusted

# Fetch data
[inc_yoy_avg_growth_df, inc_yrly_growth_df] = get_inc_3yr_avg_growth_df(yf_data)
string_pos = get_string_pos(inc_yoy_avg_growth_df)
inc_yoy_avg_growth_df_adjusted = adjust_inc_growth_df(inc_yoy_avg_growth_df)

# Display on page
if string_pos != None:
    st.subheader('Income/ revenue growth{}'.format(string_pos))
    st.dataframe(inc_yoy_avg_growth_df_adjusted) # Display table (rounded to 2 dp)
    #st.dataframe(inc_yrly_growth_df) # Display table (rounded to 2 dp)
    st.subheader('% Income Growth from previous year')
    yoy_inc = px.line(inc_yrly_growth_df, x='year', y='income', text='income',
                      labels={'year':"Year","income":"Annual Income Growth (from previous yr)"})
    yoy_inc.update_traces(textposition='top right') # Annotations for actual values
    yoy_inc.update_layout(height=500) # Set height of chart
    st.plotly_chart(yoy_inc)

#### Dividends
# Cache functions
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_dividends_df(yf_data):
    dividends_df = yf_data.get_dividends()
    return dividends_df

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_div_trend(dividends_df):
    div_5yr = dividends_df.loc[dividends_df['Dividend Type']=='5-yr average',['Values']].values[0,0]
    div_trail = dividends_df.loc[dividends_df['Dividend Type']=='Trailing',['Values']].values[0,0]
    div_forward = dividends_df.loc[dividends_df['Dividend Type']=='Forward',['Values']].values[0,0]
    # Track which dividends return null values
    divds = {'div_5yr':div_5yr,
             'div_trail':div_trail,
             'div_forward':div_forward}
    div_usable = {}
    for div_type in divds.keys():
        div_usable[div_type] = True
        if divds[div_type] == None:
            div_usable[div_type] = False
        elif math.isnan(divds[div_type]):
            div_usable[div_type] = False

    # Get trend
    if sum(div_usable.values()) <=1:
        div_trend = 'No trend available'
    elif div_trail > div_forward:
        if math.isnan(div_5yr):
            div_trend = 'FALLING'
        elif div_5yr > div_trail:
            div_trend = 'FALLING'
        else:
            div_trend = 'FLUCTUATING'
    elif div_trail < div_forward:
        if math.isnan(div_5yr):
            div_trend = 'RISING'
        elif div_5yr < div_trail:
            div_trend = 'RISING'
        else:
            div_trend = 'FLUCTUATING'
    elif div_trail-div_forward<=0.02 or div_forward-div_trail<=0.02:
        if math.isnan(div_5yr):
            div_trend = 'FLAT'
        elif div_trail-div_5yr<=0.02 or div_5yr-div_trail<=0.02:
            div_trend = 'FLAT'
        else:
            div_trend = 'FLUCTUATING'
    else:
        div_trend = 'FLUCTUATING'

    # Print divdend value to screen
    for div_type in divds.keys():
        if div_usable[div_type] == True:
            value = divds[div_type]
            if div_type in ['div_5yr', 'div_trail']:
                div_trend += ' from {}%'.format(value)
            elif div_type == 'div_forward':
                div_trend += ' (expect {}%)'.format(value)
            break

    return div_trend

# Add a placeholder to show viewer that page is loading
latest_iteration = st.empty()
bar = st.progress(0)
for i in range(100):
  # Update the progress bar with each iteration.
  latest_iteration.text(f'Loading data {i+1}%...')
  bar.progress(i + 1)
  time.sleep(0.01)
latest_iteration.empty()
bar.empty() # Remove placeholder

# Fetch data
dividends_df = get_dividends_df(yf_data)
#st.dataframe(dividends_df)
div_trend = get_div_trend(dividends_df)

# Display on page
st.subheader('Dividend Yield (%): {}'.format(div_trend))
# Plot line graph
if pd.isna(dividends_df['Values']).sum() == 3:
    st.write('No dividends data available')
else:
    fig_stock_divd = px.line(dividends_df, x='Dividend Type', y='Values', text='Values',
                  labels={'Dividend Type':"Dividend Type","Values":"Yield (%)"})
    fig_stock_divd.update_traces(textposition='top right') # Annotations for actual values
    fig_stock_divd.update_layout(
        height=500 #,
         #title={
         #   'text': "Dividend Yield (% over time)",
         #   'y':0.95,
         #   'x':0.5,
         #   'xanchor': 'center',
         #   'yanchor': 'top'}
    ) # Set height of chart
    st.plotly_chart(fig_stock_divd) # Plot chart

#### Plot prices
# Cache functions
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_current_price(yf_data):
    current_price = yf_data.get_askprice()
    return current_price

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_short_name(yf_data):
    short_name = yf_data.get_name_short()
    return short_name

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_url_tprice(sgi_data, sgx_symbol, short_name, sector):
    url_tprice = sgi_data.get_sginvestor_url(sgx_symbol, short_name, sector)
    return url_tprice

@st.cache(allow_output_mutation=True, suppress_st_warning=True, hash_funcs={"bs4.element.ContentMetaAttributeValue": id})
def get_soup(sgi_data, url_tprice):
    soup_tprice = sgi_data.get_soup_tprice(url_tprice)
    return soup_tprice

@st.cache(allow_output_mutation=True, suppress_st_warning=True, hash_funcs={"bs4.element.ContentMetaAttributeValue": id,"bs4.element.CharsetMetaAttributeValue": id})
def get_tprices_df(sgi_data, soup_tprice):
    tprices_df = sgi_data.get_tprices_df(soup_tprice)
    return tprices_df

@st.cache(allow_output_mutation=True, suppress_st_warning=True, hash_funcs={"bs4.element.ContentMetaAttributeValue": id,"bs4.element.CharsetMetaAttributeValue": id})
def get_stock_prices_all_df(sgi_data, soup_tprice, tprices_df):
    stock_prices_all_df = sgi_data.get_stock_prices_all_df(soup_tprice, tprices_df) # For display in box plot
    return stock_prices_all_df

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_avg_tprices_all_df(sgi_data, tprices_df):
    avg_tprices_all_df = sgi_data.get_avg_tprices(tprices_df) # Average and median among target prices
    return avg_tprices_all_df

@st.cache(allow_output_mutation=True, suppress_st_warning=True, hash_funcs={"bs4.element.ContentMetaAttributeValue": id,"bs4.element.CharsetMetaAttributeValue": id})
def get_tpcalls(sgi_data, soup_tprice):
    tpcalls = sgi_data.get_tpcalls(soup_tprice)
    return tpcalls

@st.cache(allow_output_mutation=True, suppress_st_warning=True, hash_funcs={"bs4.element.ContentMetaAttributeValue": id,"bs4.element.CharsetMetaAttributeValue": id})
def get_tpcalls_df(sgi_data, tpcalls):
    tpcalls_df = sgi_data.get_tpcalls_df(tpcalls)
    return tpcalls_df

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_strategies_summary(sgi_data, tpcalls_df):
    strategies_summary = sgi_data.get_strategies_summary(tpcalls_df)
    return strategies_summary

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_recommendation_msg(sgi_data, strategies_summary):
    recommendation_msg= sgi_data.get_recommendation_msg(strategies_summary)
    return recommendation_msg

# Display on page
st.subheader('Analyst calls')

# Progress placeholder to show viewer that page is loading
latest_iteration2 = st.empty()
bar2 = st.progress(0)
for i in range(100):
  # Update the progress bar with each iteration.
  latest_iteration2.text(f'Extracting bank analyses. Loading {i+1}%...')
  bar2.progress(i + 1)
  time.sleep(0.08)
latest_iteration2.empty()
bar2.empty() # Remove placeholder

# Fetch data
current_price = get_current_price(yf_data)
short_name = get_short_name(yf_data)
sgi_data = get_sgi_data.Data(sgx_symbol, short_name)
url_tprice = get_url_tprice(sgi_data, sgx_symbol, short_name, sector)
soup_tprice = get_soup(sgi_data, url_tprice)
tprices_df = get_tprices_df(sgi_data, soup_tprice)
stock_prices_all_df = get_stock_prices_all_df(sgi_data, soup_tprice, tprices_df)
avg_tprices_all_df = get_avg_tprices_all_df(sgi_data, tprices_df)
tpcalls = get_tpcalls(sgi_data, soup_tprice)
tpcalls_df = get_tpcalls_df(sgi_data,tpcalls)
strategies_summary = get_strategies_summary(sgi_data, tpcalls_df)
recommendation_msg = get_recommendation_msg(sgi_data, strategies_summary)
# Display on webpage
st.subheader('Overall recommendation - {}'.format(recommendation_msg.upper())) # Overall recommendation
st.dataframe(strategies_summary)
# Progress placeholder to show viewer that page is loading
latest_iteration3 = st.empty()
bar3 = st.progress(0)
for i in range(100):
  # Update the progress bar with each iteration.
  latest_iteration3.text(f'Loading data {i+1}%...')
  bar3.progress(i + 1)
  time.sleep(0.02)
latest_iteration3.empty()
bar3.empty() # Remove placeholder

# Show pie chart of target calls
st.markdown('Summary of calls')
if not tpcalls_df.empty:
    fig_tpcalls = px.pie(tpcalls_df, values='Tally(%)', names='Recommendation',custom_data=['Tally'],
                         color_discrete_sequence=px.colors.sequential.haline)
    fig_tpcalls.update_traces(textposition='inside', textinfo='label+percent',
                     hovertemplate = "Tally: %{customdata}")
    st.plotly_chart(fig_tpcalls)
# Open URL in new page
st.markdown('Data from {}'.format(url_tprice))
# Target calls
st.subheader("Stock prices")
# Current ask price
st.subheader('Current ask: {}'.format(current_price)) # Current price
# Average and median target prices
st.subheader('Analyst targets')
print_avg_tprices = True
for price in avg_tprices_all_df.values[0]:
    if price == None:
        print_avg_tprices = False
        break
if print_avg_tprices == True:
    st.dataframe(avg_tprices_all_df.style.format("{:.3}"))  # rounded to 2 dp
else:
    st.markdown('None available')
# Show box plot
st.subheader('Historical stock prices')
fig_stock_prices = px.box(stock_prices_all_df, x="Time", y="Value", color="Time",points="all",
                          hover_data = {"Time":False,"Range":True,"Value":True},labels={'Time':'Time','Value':'Price'},boxmode="overlay")
fig_stock_prices.update_layout(height=500)
st.plotly_chart(fig_stock_prices)

### Company health
# Cache functions
# =============================================================================
# @st.cache(allow_output_mutation=True, suppress_st_warning=True)
# def get_driver():
#     # Initialize driver
#     driver_options = Options()
#     driver_options.add_argument("--headless")
#     chromedriver_path = '/usr/local/bin/chromedriver'
#     driver = webdriver.Chrome(chromedriver_path,options=driver_options)
#     return driver
# =============================================================================

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def get_health_metrics_df(sgx_symbol):
    all_data = pd.read_csv('data/sector_summaries/All.csv', index_col=False)
    health_metrics_df = all_data.loc[all_data['Symbol']==sgx_symbol,['Price/Cash Flow','Debt/Equity','Interest Coverage']]
    return health_metrics_df

st.subheader('Company health')
#driver = get_driver()
health_metrics_df = get_health_metrics_df(sgx_symbol)
st.dataframe(health_metrics_df.style.format('{:.2f}'))
#driver.quit() # Test if this should remain