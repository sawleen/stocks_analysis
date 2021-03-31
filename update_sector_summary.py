#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 17:37:51 2020

@author: sawleen
"""
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
os.chdir('/Users/sawleen/Documents/Leen/Python/stock_analysis')
import data.get_yf_data as get_yf_data #Configured to the same root folder where display_webpg.py resides
import data.get_sgi_data as get_sgi_data #Configured to the same root folder where display_webpg.py resides
import data.get_morningstar_data as get_ms_data
import time
import math

class Update():
    #### Get sector summaries (generate main list)
    def prep_sector_summaries(self, stocks_map, stock_sectors, new_sectors, new_stocks=None):
        summary_all_df = pd.DataFrame([]) # To track for all sectors
        start_time = time.time()

        # New entries detected
        if new_sectors != 'All':
            summary_all_df = pd.read_csv('data/sector_summaries/All.csv', index_col=None)

            # Get all health metrics first
            # Health metrics require selenium, which is prone to disconnections
            health_metrics_dict_all = self.get_all_health_metrics(new_stocks)

            for sector_to_update in new_sectors:
                print('Sector to update: {}'.format(sector_to_update))
                summary_df = pd.read_csv('data/sector_summaries/{}.csv'.format(sector_to_update), index_col=None)
                for symbol in new_stocks:
                    # Update CSV for indiv sector
                    current_sector = stocks_map.loc[stocks_map['SGX_Symbol'] == symbol, ['Sector']].values[0][0]
                    print('Current stock sector: {}'.format(current_sector))
                    if current_sector == sector_to_update:
                        stocks_map_filtered = stocks_map.loc[stocks_map['SGX_Symbol'] == symbol, stocks_map.columns]
                        [summary_df, summary_all_df] = self.get_summary_df(sector_to_update, stocks_map_filtered, health_metrics_dict_all, summary_df, summary_all_df)
                # Sector summary
                summary_df.sort_values(['Strategy','Tally','Tally(%)','Dividend (fwd)','PB Ratio'],ascending=[True,False,False,False,True],inplace=True)
                summary_df.to_csv('data/sector_summaries/{}.csv'.format(sector_to_update), index=False)

            summary_all_df.sort_values(['Strategy','Tally','Tally(%)','Dividend (fwd)','PB Ratio'],ascending=[True,False,False,False,True],inplace=True)
            summary_all_df.to_csv('data/sector_summaries/All.csv',index=False)
         # No new entries but update for ALL sectors
        else:
            #expected_runtime = int(len(stocks_map)/60*15) # expected time to print to screen
            print('Updating summary for all sectors...')
            #print('Please hold on for about {}min...'.format(expected_runtime))
            summary_all_df = pd.DataFrame([])

            # Get all health metrics first
            # Health metrics require selenium, which is prone to disconnections
            symbols=stocks_map['SGX_Symbol']
            health_metrics_dict_all = self.get_all_health_metrics(symbols)

            for sector in stock_sectors:
                summary_df = pd.DataFrame([])
                if sector!= 'All':
                    stocks_map_filtered = stocks_map.loc[stocks_map['Sector'] == sector, stocks_map.columns]
                    [summary_df, summary_all_df] = self.get_summary_df(sector, stocks_map_filtered, health_metrics_dict_all, summary_df, summary_all_df)
                    # Sector summary
                    summary_df.sort_values(['Strategy','Tally','Tally(%)','Dividend (fwd)','PB Ratio'],ascending=[True,False,False,False,True],inplace=True)
                    summary_df.to_csv('data/sector_summaries/{}.csv'.format(sector), index=False)

            # All stocks summary
            print('Sorting sector summary for ALL stocks...')
            summary_all_df.sort_values(['Strategy','Tally','Tally(%)','Dividend (fwd)','PB Ratio'],ascending=[True,False,False,False,True],inplace=True)
            summary_all_df.to_csv('data/sector_summaries/All.csv', index=False)

        total_time = round((time.time() - start_time)/60,2)
        print('Total time taken: {}'.format(total_time))
    #### End of prep_sector_summaries

    def get_summary_df(self, sector_to_update, stocks_map_filtered, health_metrics_dict_all, summary_df, summary_all_df):
        print('Prepping sector summary for {}...'.format(sector_to_update))

        for sgx_symbol in stocks_map_filtered['SGX_Symbol']:
            print('{}...'.format(sgx_symbol))
            yf_data = get_yf_data.Data(sgx_symbol)
            industry = yf_data.get_industry()
            stats = yf_data.get_basic_stats()
            [inc_yoy_avg_growth_df, inc_yrly_growth_df] = yf_data.process_inc_statement()
            dividends_df = yf_data.get_dividends()
            try:
                div_fwd = dividends_df.loc[dividends_df['Dividend Type']=='Forward',['Values']].values[0][0]
            except:
                print('! Warning: No forward dividend data fetched for {}'.format(sgx_symbol))
                div_fwd = math.nan

            short_name = yf_data.get_name_short()
            disp_name = yf_data.get_name_disp()
            if '.SI' in sgx_symbol and type(short_name)==str:
                sgi_data = get_sgi_data.Data(sgx_symbol, short_name)
                url_tprice = sgi_data.get_sginvestor_url(sgx_symbol, short_name, industry)
                #print(url_tprice)
                soup_tprice = sgi_data.get_soup_tprice(url_tprice)
                tpcalls = sgi_data.get_tpcalls(soup_tprice)
                tpcalls_df = sgi_data.get_tpcalls_df(tpcalls)
                strategies_summary = sgi_data.get_strategies_summary(tpcalls_df)
            else: # create empty dataframe
                strategies_summary = pd.DataFrame(index=[0],columns=['Strategy','Tally(%)','Tally'])

            health_metrics = health_metrics_dict_all[sgx_symbol]

            info={'Name':disp_name,
                  'Symbol':sgx_symbol,
                  'Market Cap (bil)':stats['Market Cap (bil)'],
                  'PB Ratio': stats['PB Ratio'],
                  'PE Ratio': stats['PE Ratio'],
                  'Dividend Payout Ratio': stats['Dividend Payout Ratio'],
                  'Income Growth (Avg YoY)':inc_yoy_avg_growth_df['Income'].values[0],
                  'ROE': stats['% Return on Equity'],
                  'Dividend (fwd)': div_fwd,
                  'Strategy': strategies_summary.at[0,'Strategy'],
                  'Tally(%)': strategies_summary.at[0,'Tally(%)'],
                  'Tally': strategies_summary.at[0,'Tally'],
                  'Price/Cash Flow':health_metrics['Price/Cash Flow'],
                  'Debt/Equity':health_metrics['Debt/Equity'],
                  'Interest Coverage':health_metrics['Interest Coverage']}
            # Stock summary
            info_df = pd.DataFrame.from_dict(info, orient='columns')
            # Sector summary
            if summary_df.empty:
                summary_df = info_df
            else:
                summary_df = pd.concat([summary_df, info_df])
            # All sector summary
            if summary_all_df.empty:
                summary_all_df = info_df
            else:
                summary_all_df = pd.concat([summary_all_df, info_df])

        return [summary_df, summary_all_df]

    def get_all_health_metrics(self, symbols):
        print('Do you want to read from pre-generated health metrics?')
        user_pref = input()

        print('... Getting health metrics...')
        # Read from stored data if user wants to save time
        if 'y' in user_pref.lower():
            print('...from CSV...')
            health_metrics_all_df = pd.read_csv('data/health_metrics_all_df.csv',index_col='symbol')
            health_metrics_dict_all = health_metrics_all_df.to_dict('index')

        else:
            # Initialize driver
            driver_options = Options()
            driver_options.add_argument("--headless") #for chromedriver to work remotely
            chromedriver_path = '/usr/local/bin/chromedriver'
            driver = webdriver.Chrome(chromedriver_path,options=driver_options)
            # Get health metrics
            health_metrics_dict_all={}
            for sgx_symbol in symbols:
                print('...{}...'.format(sgx_symbol))
                health_metrics_dict = get_ms_data.Data().get_health_metrics_dict(sgx_symbol, driver)
                health_metrics_dict_all[sgx_symbol] = health_metrics_dict
            # Close driver
            driver.quit()
            print('... Metrics stored...')
            print(health_metrics_dict_all)
            # Option to save to CSV if user wants
            print('... Do you want to save to local disk?')
            save_health_metrics = input()

            if 'y' in save_health_metrics.lower():
                #print(health_metrics_dict_all)
                # Write to CSV in case want to refer in future
                health_metrics_dict_df = pd.DataFrame.from_dict(health_metrics_dict_all).T
                health_metrics_dict_df.index.rename('symbol',inplace=True)
                #health_metrics_dict_df.reset_index(inplace=True)

                saved_health_metrics = pd.read_csv('data/health_metrics_all_df.csv', index_col=['symbol'])
                for sgx_symbol in symbols:
                    print(sgx_symbol)
                    # Add to saved list if not already inside
                    if not sgx_symbol in saved_health_metrics.index:
                        health_metric_symbol = health_metrics_dict_df[health_metrics_dict_df.index==sgx_symbol]
                        saved_health_metrics = pd.concat([saved_health_metrics, health_metric_symbol])
                    # Update list if already inside
                    else:
                        saved_health_metrics[saved_health_metrics.index==sgx_symbol] = health_metrics_dict_df[health_metrics_dict_df.index==sgx_symbol]
                #health_metrics_dict_df.sort_index(inplace=True)
                #health_metrics_dict_df.to_csv('data/health_metrics_all_df.csv')
                saved_health_metrics.sort_index(inplace=True)
                saved_health_metrics.to_csv('data/health_metrics_all_df.csv')

        return health_metrics_dict_all