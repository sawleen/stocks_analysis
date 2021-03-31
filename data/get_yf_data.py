#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 16:28:08 2020

@author: sawleen
"""
import yfinance as yf
import pandas as pd
from datetime import date as _date
from dateutil.relativedelta import relativedelta as _relativedelta
import math as _math
#pd.set_option('display.max_columns', 200)

class Data():
    def __init__ (self, sgx_symbol):
        self.sgx_symbol = sgx_symbol
        self.stock = yf.Ticker("{}".format(sgx_symbol))

    def get_name_disp(self):
        stock = self.stock
        try:
            return stock.info['longName']  # for display
        except:
            print('! Warning: No name fetched for {}'.format(self.sgx_symbol))
            return self.sgx_symbol

    def get_name_short(self):
        stock = self.stock
        try:
            short_name = stock.info['shortName'] # for feeding into SG Investor URL
            short_name = short_name.lower()
            short_name = short_name.replace(' ','-')
            return short_name
        except:
            print('! Warning: Short name cannot be fetched for {}'.format(self.sgx_symbol))
            return None

    def get_sector(self):
        stock = self.stock
        try:
            return stock.info['sector']
        except:
            print('Stock {} has no sector info'.format(self.sgx_symbol))
            return None

    # Mainly for REITS
    def get_industry(self):
        stock = self.stock
        try:
            return stock.info['industry']
        except:
            print('Stock {} has no industry info'.format(self.sgx_symbol))
            return None

    # Get basic stats
    def get_basic_stats(self):
        stock = self.stock
        # Financial ratios
        market_cap = _math.nan # Set to nan if value not in stock info
        pb_ratio = _math.nan
        pe_ratio = _math.nan
        payout_ratio = _math.nan
        roe = _math.nan
        percentage_insider_share = _math.nan

        try:
            if 'marketCap' in stock.info.keys() and stock.info['marketCap']!=None:
                market_cap = round(stock.info['marketCap']/(10**9),2)
            if 'priceToBook' in stock.info.keys():
                pb_ratio = round(stock.info['priceToBook'],2)
            if 'trailingPE' in stock.info.keys():
                pe_ratio = round(stock.info['trailingPE'],2)
            if 'payoutRatio' in stock.info.keys():
                payout_ratio = stock.info['payoutRatio']
                if payout_ratio == None:
                    payout_ratio = _math.nan
                else:
                    payout_ratio = payout_ratio*100
            if 'returnOnEquity' in stock.info.keys():
                roe = stock.info['returnOnEquity']
                if roe:
                    roe = round(roe*100,2)

        except Exception as e:
            print(e)

        try: #sometimes the data can't be loaded for some reason :/
            percentage_insider_share = stock.major_holders.iloc[0,0]
            percentage_insider_share = percentage_insider_share.replace('%','')
            percentage_insider_share = float(percentage_insider_share)
            percentage_insider_share = round(percentage_insider_share,2)
        except:
            print('! Warning: Percentage insider share for {} cannot be loaded.. '.format(self.sgx_symbol))
            print('Data fetched instead:')
            print('{}'.format(percentage_insider_share))
            pass


        stats={'Market Cap (bil)':market_cap,
               'PB Ratio':pb_ratio,
           'PE Ratio':pe_ratio,
           'Dividend Payout Ratio':payout_ratio,
           '% Return on Equity': roe,
           '% insider shares':percentage_insider_share}
           #'PEG Ratio':peg_ratio

        stats_df = pd.DataFrame.from_dict(stats, orient='index')
        stats_df.columns = ['Values']
        stats_df = stats_df.T

        return stats_df

    # Get dividends
    def get_dividends(self):
        stock = self.stock
        # Dividends
        try:
            div_yield = stock.info['dividendYield']
            div_yield_trail = stock.info['trailingAnnualDividendYield']
            div_yield_5yr = stock.info['fiveYearAvgDividendYield']

            dividends = {'5-yr average':div_yield_5yr,
                         'Trailing':div_yield_trail,
                         'Forward':div_yield}

            for div_type in dividends:
                if dividends[div_type] != None:
                    if dividends[div_type] >1:
                        dividends[div_type] = round(dividends[div_type],2)
                    else:
                        dividends[div_type] = round(dividends[div_type]*100,2) # Convert % into figure

            dividends_df = pd.DataFrame.from_dict(dividends, orient='index')
            dividends_df=dividends_df.reset_index() # Set index(dividend type) to a column
            dividends_df.columns=['Dividend Type','Values']
        except:
            print('! Warning: Dividend data cannot be fetched for {}'.format(self.sgx_symbol))
            dividends_df = pd.DataFrame(index = ['5-yr average','Trailing','Forward'], columns=['Dividend Type','Values'])

        return dividends_df

    # Current stock price
    def get_askprice(self):
        stock=self.stock
        try:
            return stock.info['ask'] # Current price
        except:
            print('! Warning: Ask price cannot be fetched for {}'.format(self.sgx_symbol))
            return None

    # Return average growth over 3 years for both income and revenue
    def process_inc_statement(self):
        inc_statement = self.get_inc_statement()
        inc_yoy_avg_growth={}
        inc_yrly_growth={}

        for fig_type in inc_statement:
            figures = inc_statement[fig_type]
            yrly_figures = self.get_yrly_figures(figures)
            all_years = self.get_years(yrly_figures)
            yrly_growth = self.calc_yrly_growth(yrly_figures, all_years, fig_type)
            inc_yrly_growth[fig_type] = yrly_growth
            growth_yoy_avg = self.calc_yoy_avg_growth(yrly_figures, all_years, fig_type)
            inc_yoy_avg_growth[fig_type] = growth_yoy_avg

        # Average yoy growth
        inc_yoy_avg_growth_df = pd.DataFrame.from_dict(inc_yoy_avg_growth,orient='index')

        try:
            first_year = all_years[0]
            last_year = all_years[-1]
        except:
            first_year = ''
            last_year = ''

        inc_yoy_avg_growth_df.columns=['Average YoY Growth ({}-{})'.format(first_year, last_year)] #Rename
        inc_yoy_avg_growth_df = inc_yoy_avg_growth_df.T #Transpose
        inc_yoy_avg_growth_df = inc_yoy_avg_growth_df[['income','revenue']] #Reorder columns
        inc_yoy_avg_growth_df.columns=['Income','Revenue'] #Rename columns

        # Average yoy growth
        inc_yrly_growth_df = pd.DataFrame.from_dict(inc_yrly_growth,orient='index').T
        #inc_yrly_growth_df.index.rename('year',inplace=True)
        inc_yrly_growth_df=inc_yrly_growth_df.reset_index()
        inc_yrly_growth_df.rename(columns={'index':'year'},inplace=True)

        return [inc_yoy_avg_growth_df, inc_yrly_growth_df]

    #### Sub-functions for process_inc_statement
    # Get gross profit and total revenue
    def get_inc_statement(self):
        stock=self.stock
        try:
            income = stock.financials.loc[['Gross Profit']]
            revenue = stock.financials.loc[['Total Revenue']]
        except:
            print('! Warning: Income and revenue cannot be fetched for {}'.format(self.sgx_symbol))
            income = pd.DataFrame([])
            revenue = pd.DataFrame([])

        inc_statement={'income':income,
                       'revenue':revenue}
        return inc_statement

    # Tag dataframe figures to correct year
    def get_yrly_figures(self, figures):
        # Convert dataframe to dictionary for yearly figures
        yrly_figures={}
        no_of_records = len(figures.columns)

        for num in range(no_of_records):
            year = figures.columns[num].year
            value = figures.iat[0,num]
            yrly_figures[year] = round(value,0)
        return yrly_figures

    # Get years in data
    def get_years(self, yrly_figures):
        all_years = sorted(list(yrly_figures.keys()))
        return all_years

    # Calculate yoy growth in revenue or income
    def calc_yrly_growth(self, yrly_figures, all_years, fig_type):
        # Get yoy growth
        yrly_growth = {}

        try:
            if len(all_years)>1:
                years_without_first = all_years[1:]
                for i in range(len(years_without_first)):
                    current_year = years_without_first[i]
                    previous_year = all_years[i]
                    growth = (yrly_figures[current_year] - yrly_figures[previous_year])/yrly_figures[previous_year]
                    growth = round(growth*100,2)
                    yrly_growth[current_year] = growth/(current_year-previous_year)
        except:
            print('! Warning: No yearly growth data fetched for {} {}'.format(self.sgx_symbol, fig_type))
            print('No yrly growth from data below:')
            print(yrly_figures)
            pass

        return yrly_growth

    # Calculate average growth over 3 years (for revenue or income)
    def calc_yoy_avg_growth(self, yrly_figures, all_years, fig_type):
        try:
            first_year = all_years[0]
            last_year = all_years[-1]
            num_years = last_year - first_year

            # Get avg growth over 3 yrs
            if len(all_years)>1:
                growth_yoy_avg = (yrly_figures[last_year]- yrly_figures[first_year])/yrly_figures[first_year]
                growth_yoy_avg = round(growth_yoy_avg/num_years*100,2)

                return growth_yoy_avg
            else:
                return None
        except:
            print('! Warning: Yoy Avg Growth not fetched for {} {}'.format(self.sgx_symbol, fig_type))
            print('No yoy avg growth from data below:')
            print(yrly_figures)
            return None
    #### End of sub-functions for process_inc_statement

    # Historical prices over different time ranges
    def get_interval_history(self, today, today_date, stock, interval):
        var_high = _math.nan
        var_low = _math.nan
        current = today
        while _math.isnan(var_high) or _math.isnan(var_low):
            if interval=='mo':
                back_1_interval= current+_relativedelta(months=-1)
            elif interval=='wk':
                back_1_interval= current+_relativedelta(days=-7)
            back_1_interval_date = back_1_interval.strftime("%Y-%m-%d")

            try:
                stock_interval = stock.history(interval="1{}".format(interval), start=back_1_interval_date, end=today_date)
                var_high = stock_interval.iloc[0,1]
                var_low = stock_interval.iloc[0,2]
                current = back_1_interval
            except:
                var_high = _math.nan
                var_low = _math.nan
                break

        #print(stock_interval)
        interval_history = {'low':var_low,
                   'high':var_high}
        return interval_history

    def get_prices(self):
        stock=self.stock
        today = _date.today()
        today_date = today.strftime("%Y-%m-%d")
        # Past 5 years
        try:
            price_5yr=stock.history(period="5Y")
            fiveyr_high = max(price_5yr['High'])
            fiveyr_low = min(price_5yr['Low'])
        except:
            fiveyr_high = _math.nan
            fiveyr_low = _math.nan

        # Yearly
        try:
            yr_high = stock.info['fiftyTwoWeekHigh']
        except:
            yr_high = _math.nan

        try:
            yr_low = stock.info['fiftyTwoWeekLow']
        except:
            yr_low = _math.nan
        # Monthly
        mo_results = self.get_interval_history(today, today_date, stock, interval='mo')

        # Weekly
        wk_results = self.get_interval_history(today, today_date, stock, interval='wk')

        # Daily
        try:
            day_high = stock.info['dayHigh']
        except:
            day_high = _math.nan
        try:
            day_low = stock.info['dayLow']
        except:
            day_low = _math.nan
        try:
            current = stock.info['ask']
        except:
            current = _math.nan

        prices = {'day':{'low':day_low,
                        'high':day_high},
                'wk':wk_results,
                'mo':mo_results,
                'yr':{'low':yr_low,
                      'high':yr_high},
                'five-yr':{'low':fiveyr_high,
                        'high':fiveyr_low}}

        # Convert to dataframe
        stock_prices_df = pd.DataFrame.from_dict(prices, orient='index')
        stock_prices_df=stock_prices_df.reset_index()
        stock_prices_df.columns=['time','low','high']
        stock_prices_melt = pd.melt(stock_prices_df,id_vars=['time'],value_vars=['low','high'])
        stock_prices_melt.columns = ['Time','Range','Value']

        # Get moving averages
        sma = self.get_sma()
        sma_df = pd.DataFrame.from_dict(sma, orient='index')
        sma_df = sma_df.reset_index()
        sma_df.columns=['Range','Value']
        sma_df['Time']=''
        sma_df.loc[sma_df['Range']=='50 day',['Time']] = '50d sma'
        sma_df.loc[sma_df['Range']=='200 day',['Time']] = '200d sma'
        sma_df['Value'] = sma_df['Value'].round(2)
        sma_df = sma_df[['Time','Range','Value']]
        # Combine
        stock_prices_all = pd.concat([stock_prices_melt,sma_df])
        stock_prices_all = stock_prices_all.append({'Time':'current', 'Range':'NA','Value':current},ignore_index=True) # Add current price

        return stock_prices_all

    # Sub-function for Moving averages
    def get_sma(self):
        stock = self.stock
        # Moving averages
        try:
            sma_50 = stock.info['fiftyDayAverage']
            sma_200 = stock.info['twoHundredDayAverage']
        except:
            print('! Warning: Moving averages cannot be fetched for {}'.format(self.sgx_symbol))
            sma_50 = _math.nan
            sma_200 = _math.nan

        sma = {'50 day':sma_50,
                 '200 day':sma_200}
        return sma

    #Get 5-year history
#    def get_5yr_prices(self):
#        stock = self.stock
#        price_5yr=stock.history(period="5Y")
#        max(price_5yr['High'])
#        min(price_5yr['Low'])

# get free cash flow, debt to equity ratio, interest coverage ratio
        #https://algotrading101.com/learn/yahoo-finance-api-guide/