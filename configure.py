#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 22:06:04 2020

@author: sawleen
"""
import pandas as pd
import os
os.chdir('/Users/sawleen/Documents/Leen/Python/stock_analysis')
import data.get_yf_data as get_yf_data #Configured to the same root folder where display_webpg.py resides

class Configure():
    def prep_CSV(self):
        # Read CSV and detect missing values that require updating
        stocks_map = pd.read_csv('data/stocks_map.csv',index_col=None)
        stocks_map.drop_duplicates(subset=['SGX_Symbol'],inplace=True) # Drop duplicates
        missing_stocks = stocks_map.loc[pd.isna(stocks_map['Name']) | pd.isna(stocks_map['Sector']),stocks_map.columns]
        print('Detected new entries in CSV: {} ....'.format(len(missing_stocks)))
        # Update CSV if necessary
        new_stocks = []
        new_sectors = [] # to save new sectors
        for i in missing_stocks.index:
            sgx_symbol = stocks_map.at[i,'SGX_Symbol']
            print('Updating {} ...'.format(sgx_symbol))
            yf_data = get_yf_data.Data(sgx_symbol)
            this_name = missing_stocks.at[i,'Name']
            this_sector = missing_stocks.at[i,'Sector']

            if type(this_name)!=str:
                stocks_map.at[i,'Name'] = yf_data.get_name_disp()
            if type(this_sector)!=str:
                new_sector = yf_data.get_sector()
                stocks_map.at[i,'Sector'] = new_sector
                new_sectors.append(new_sector)
                new_stocks.append(sgx_symbol)
        # Export CSV and report
        if len(missing_stocks)>0:
            print('Saving to CSV...')
            stocks_map.sort_values('Name', ascending=True, inplace=True)
            stocks_map.to_csv('data/stocks_map.csv',index=False)
            print('CSV has been updated')
        # Remove duplicates from new_sectors
        new_sectors = list(dict.fromkeys(new_sectors))
        new_stocks = list(dict.fromkeys(new_stocks))
        return [stocks_map, new_stocks, new_sectors]

    def get_all_sectors(self,stocks_map):
        print('Fetching all stock sectors...')
        stock_sectors = list(stocks_map['Sector'].unique())
        stock_sectors.append('All')
        stock_sectors = sorted(stock_sectors)
        stock_sectors_df = pd.DataFrame(stock_sectors)
        stock_sectors_df.columns=['Sector']
        stock_sectors_df.to_csv('data/stock_sectors.csv',index=False)

        return stock_sectors

#if __name__ == "__main__":
#    main()