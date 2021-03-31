#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 21:41:48 2020

@author: sawleen
"""
import time
import math
from selenium.webdriver.common.by import By

class Data():
    def __init__(self):
        pass

    # splits strings into alphabets and numbers
    def split_string(self,s):
        segments = []
        char = ""
        num = ""
        for letter in s:
            if letter.isdigit():
                if char:
                    segments.append(char)
                    char = ""
                num += letter
            else:
                if num:
                    segments.append(num)
                    num = ""
                char += letter
        if char:
            segments.append(char)
        else:
            segments.append(num)

        ms_string = ''
        for s in segments:
            ms_string += s + '-'
        ms_string = ms_string[:-1]

        return ms_string


    def get_health_metrics_dict(self,sgx_symbol, driver):
        # Get morningstar url
        sgx_symbol_read=sgx_symbol.replace('.SI','')
        ms_string = self.split_string(sgx_symbol_read)

        url='https://www.morningstar.com/stocks/xses/{}/financials'.format(ms_string)
        #print(url)
        driver.get(url)
        time.sleep(3.2) # To give time to download data
        elements = driver.find_elements(By.CLASS_NAME, 'dp-pair')
        health_metrics_dict={}
        for e in elements:
            #print(e.text)
            if e.text !='':
                metric = e.text.split('\n')
                metric_name = metric[0]
                if metric_name in ['Price/Cash Flow','Debt/Equity', 'Interest Coverage']:
                    metric_value = metric[1]
                    if metric_value == "—":
                        metric_value=math.nan
                    health_metrics_dict[metric_name] = metric_value
        for metric_name in ['Price/Cash Flow','Debt/Equity', 'Interest Coverage']:
            if metric_name not in health_metrics_dict.keys():
                metric_value=math.nan
                health_metrics_dict[metric_name] = metric_value

        return health_metrics_dict