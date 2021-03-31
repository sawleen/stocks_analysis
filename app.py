#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 15:28:24 2020

@author: sawleen
# To run, change working directory in Terminal first:
## "cd Documents/Leen/Python/stock_analysis"
# Next, key in "python -m app"
"""
import os
import sys
from streamlit import cli as stcli

# Important - set the right working directory before importing relevant modules
os.chdir('/Users/sawleen/Documents/Leen/Python/stock_analysis/')
#print(os.getcwd())
import configure
import update_sector_summary as update_summ

def main():
    # 1. Fetch CSV file data
    print('Configuring CSV data...')
    config = configure.Configure()
    [stocks_map, new_stocks, new_sectors] = config.prep_CSV()
    stock_sectors = config.get_all_sectors(stocks_map)

    # 2. Update sector summaries (if required)
    print('Do you want to update sector summaries for all stocks? Key in Y or N')
    user_input = input()
    if 'y' in user_input or 'Y' in user_input:
        update_sector_summaries=True
    elif 'n' in user_input or 'N' in user_input:
        update_sector_summaries=False
    else:
        print('I did not get that. Please rerun the app and key in the correct input.')
        return None

    update_secsum = update_summ.Update()
    # Update all sectors if required
    if update_sector_summaries==True:
        update_secsum.prep_sector_summaries(stocks_map, stock_sectors, 'All')
    # Else update only for new entries
    else:
        print('Detecting new sectors added...')
        print(new_sectors)
        update_secsum.prep_sector_summaries(stocks_map, stock_sectors, new_sectors, new_stocks)

    print('Data configuration complete')
    # 3. Display in webpage with streamlit
    os.chdir('/Users/sawleen/Documents/Leen/Python/stock_analysis')
    sys.argv = ["streamlit", "run", "display_webpg.py"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()