#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 21:52:39 2020

@author: sawleen
"""
# Trying to parse data from financial websites
# Import libraries
from bs4 import BeautifulSoup as _BSoup
from forex_python.converter import CurrencyRates as _CRates
import requests as _requests
import os
os.chdir('/Users/sawleen/Documents/Leen/Python/stock_analysis')
import data.get_yf_data as get_yf_data #Configured to the same root folder where display_webpg.py resides
import pandas as _pd
import re as _re
import math as _math

class Data():
    def __init__(self, sgx_symbol, short_name):
        self.sgx_symbol = sgx_symbol
        self.short_name = short_name
        #self.soup_tprice = self.get_soup_tprice(sgx_symbol, short_name)

    #### Get URL for SGInvestor page
    def get_sginvestor_url(self, sgx_symbol, short_name, industry):
        # Get stock type to feed into URL
        if 'reit' in industry.lower():
            stock_type = 'reit'
        else:
            stock_type = 'stock'

        # Drop '.SI' in SGX symbol before feeding into URL
        sgx_symbol_read=sgx_symbol.replace('.SI','')
        # Drop '-$' in short name
        short_name = short_name.replace('$-','')

        [short_name, stock_type] = self.get_url_strings(sgx_symbol_read, short_name, stock_type)
        # Read SG Investors - Target Price page
        url_tprice='https://sginvestors.io/sgx/{}/{}-{}/target-price'.format(stock_type, sgx_symbol_read, short_name)
        return url_tprice

    #### Manage exceptions for selected symbols
    def get_url_strings(self, sgx_symbol_read, short_name, stock_type):
        # Transform for Asian Healthcare Specialist
        if sgx_symbol_read=='1J3':
            short_name = short_name + ('healthcare')
        # Transform for CDL
        if sgx_symbol_read=='C09' or sgx_symbol_read=='CY6U':
            stock_type = 'stock'
        # Transform for Frasers Centrepoint Trust
        elif sgx_symbol_read=='J69U':
            short_name='frasers-cpt-tr'
        # Transform for Frasers Hospitality Trust
        elif sgx_symbol_read=='ACV':
            short_name=short_name.replace('ospitality-','')
        # Transform for Frasers Log/Com Trust
        elif sgx_symbol_read=='BUOU':
            short_name = 'frasers-lni-tr'
        # Transform for Genting
        elif sgx_symbol_read == 'G13':
            short_name += '-sing'
        # Transform for Jardine
        elif sgx_symbol_read == 'C07':
            short_name='jardine-cnc'
        # Transform for MedTecs Intl
        elif sgx_symbol_read == '546':
            short_name='medtecs-intl'
        # Transform for Netlink
        elif sgx_symbol_read == 'CJLU':
            short_name += '-nbn-tr'
        # Transform for Oxley
        elif sgx_symbol_read=='5UX':
            stock_type = 'stock'
        # Transform for Raffles Education
        elif sgx_symbol_read=='NR7':
            short_name += '-edu'
        # Transform for Raffles Medical
        elif sgx_symbol_read=='BSL':
            short_name += '-medical'
        # Transform for UOL
        #elif sgx_symbol_read=='U14':
        #    stock_type = 'stock'
        # Transform for Yanlord Land
        elif sgx_symbol_read=='Z25':
            short_name += '-land'
        #    stock_type = 'stock'

        return [short_name, stock_type]

    #### Get soup
    def get_soup_tprice(self, url_tprice):
        #### Read data from SG Investors site into Beautiful Soup
        with _requests.get(url_tprice) as r:
            html_tprice = r.text
            soup_tprice = _BSoup(html_tprice, "lxml")
        return soup_tprice

    #### Get target prices of stock
    def get_tprices_df(self, soup_tprice):
        raw_tprices= soup_tprice.find_all('div',{'class':'TPPRICE'})
        raw_brokers= soup_tprice.find_all('div',{'class':'BROKER'})
        tprices={}
        for i in range(len(raw_tprices)):
            broker=raw_brokers[i].get_text()
            tprice=raw_tprices[i].get_text()
            tprice_cleaned=tprice.replace('Price Target: ','')
            # Remove numbers that have no forecasts
            if tprice_cleaned == 'N/A':
                continue
            # Modify targets in Malaysian ringgit (Malaysian banks sometimes forecast in this)
            if tprice_cleaned.startswith('MYR'):
                tprice_cleaned = tprice_cleaned.replace('MYR','')
                # Convert from MYR to SGD
                c = _CRates()
                myr_to_sgd_rate = c.get_rate('MYR','SGD')
                tprice_cleaned = float(tprice_cleaned) * myr_to_sgd_rate
            # Convert to float
            tprice_cleaned = float(tprice_cleaned)
            tprices[broker] = tprice_cleaned

        tprices_df = _pd.DataFrame.from_dict(tprices, orient='index')
        tprices_df = tprices_df.reset_index()
        if not tprices_df.empty:
            tprices_df.columns=['Range','Value'] # To match to historical prices columns
            tprices_df['Time'] = 'target'
            tprices_df=tprices_df[['Time','Range','Value']]
        return tprices_df

    #### Get all stock prices to display in box plot
    def get_stock_prices_all_df(self, soup_tprice, tprices_df):
        yf_data = get_yf_data.Data(self.sgx_symbol)
        stock_prices_all = yf_data.get_prices()
        if tprices_df.empty:
            stock_prices_all_df  = stock_prices_all
        else:
            stock_prices_all_df=_pd.concat([stock_prices_all, tprices_df])
        # Order rows by time
        order_dict = {'target':9,
                      'current':8,
                      'day':7,
                      'wk':6,
                      'mo':5,
                      '50d sma':4,
                      '200d sma':3,
                      'yr':2,
                      'five-yr':1}
        order_dict = _pd.DataFrame.from_dict(order_dict, orient='index')
        order_dict = order_dict.reset_index()
        order_dict.columns = ['Time','order']
        stock_prices_all_df2=_pd.merge(stock_prices_all_df, order_dict,how='left',on=['Time'])
        stock_prices_all_df2.sort_values(['order'],inplace=True)

        return stock_prices_all_df2

    #### Get average target price
    def get_avg_tprices(self, tprices_df):
        avg_tprice=None
        med_tprice=None
        if not tprices_df.empty:
            tprices=tprices_df['Value'].to_list()
            tprices.sort()
            avg_tprice = round(sum(tprices)/len(tprices),2)

            index_num = _math.floor(len(tprices)/2) -1
            med_tprice = tprices[index_num] # Get median estimate

        avg_tprices_all = {'Target Prices':{'Average':avg_tprice,
                                            'Median':med_tprice}}
        avg_tprices_all_df = _pd.DataFrame.from_dict(avg_tprices_all, orient='index')
        avg_tprices_all_df = avg_tprices_all_df.round(2)
        return avg_tprices_all_df

    #### Get analysts' calls
    def get_tpcalls(self, soup_tprice):
        raw_tpcall = soup_tprice.find_all('div',{'class':_re.compile("TPCALL")})
        # Get tpcalls
        tpcalls={}
        for raw_call in raw_tpcall:
            call=raw_call.get_text()
            call_cleaned=call.replace('Rating: ','')
            call_cleaned=call_cleaned.upper()

            if call_cleaned == 'NOT RATED': # don't store not rated results
                next
            elif call_cleaned not in tpcalls:
                tpcalls[call_cleaned]=1
            else:
                tpcalls[call_cleaned]+=1

        tpcalls_sorted = sorted(tpcalls.items(), key=lambda x: x[1], reverse=True)

        return tpcalls_sorted

    #### Convert tpcalls to dataframe for display
    def get_tpcalls_df(self, tpcalls_sorted):
        tpcalls_df = _pd.DataFrame(tpcalls_sorted)
        if not tpcalls_df.empty:
            tpcalls_df.columns = ['Recommendation','Tally']
            tpcalls_df['Tally(%)'] = round(tpcalls_df['Tally']/sum(tpcalls_df['Tally'])*100,1)
            tpcalls_df['Tally(%)'] = tpcalls_df['Tally(%)'].astype('int64')
        return tpcalls_df

    #### Get summary strategy
    def get_strategies_summary(self, tpcalls_df):
        strategy_dict = {'BUY':'BUY',
                         'ACCUMULATE':'BUY',
                         'ADD':'BUY',
                         'HOLD':'HOLD',
                         'NEUTRAL':'HOLD',
                         'SELL':'SELL',
                         'REDUCE':'SELL'}
        strategy_convert = _pd.DataFrame.from_dict(strategy_dict, orient='index')
        strategy_convert.columns=['Strategy']
        #strategy_convert = strategy_convert.reset_index()

        if not tpcalls_df.empty:
            strategies_summary = _pd.DataFrame([])
            tpcalls_df2 = _pd.merge(tpcalls_df, strategy_convert, how='left', left_on='Recommendation',right_index=True)
            tpcalls_df2 = tpcalls_df2[['Strategy','Tally(%)','Tally']]
            strategies_summary = tpcalls_df2.groupby(['Strategy']).sum()
            strategies_summary['Tally(%)'] = round(strategies_summary['Tally(%)'],0)
            #strategies_summary['Tally'] = round(strategies_summary['Tally'],0)

            # Sort all strategies
            strategies_summary.sort_values(by=['Tally(%)'], ascending=False,inplace=True)
            strategies_summary.reset_index(inplace=True)
        else:
            strategies_summary = _pd.DataFrame([[None, None, None]])
            strategies_summary.columns = ['Strategy','Tally(%)','Tally']

        return strategies_summary

    #### Get overall recommendation message to display on page
    def get_recommendation_msg(self, strategies_summary):
        recommendation_msg = ''
        if not strategies_summary.empty:
            recommendation = strategies_summary['Strategy'][0]
            recommendation_percent = strategies_summary['Tally(%)'][0]
            recommendation_msg = '{} ({}%)'.format(recommendation, recommendation_percent)

            for strategy in strategies_summary['Strategy'][1:]:
                strategy_percentage = strategies_summary.loc[strategies_summary['Strategy']==strategy,['Tally(%)']].values[0,0]
                if strategy_percentage == recommendation_percent:
                    recommendation_msg += ' or {} ({}%)'.format(strategy, strategy_percentage)

        return recommendation_msg
    # End of get_recommendation