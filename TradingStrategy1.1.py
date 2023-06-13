#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import time
from datetime import datetime
from enum import Enum
import MetaTrader5 as mt5
import numpy as np
import talib
from talib import MA_Type
import logging
logger = logging.getLogger()  


# In[6]:


max_gap = 0.05500  # 最大间距,用于判断开仓
min_gap = 0.01000   # 最小间距,用于判断开仓
add_times = 3     # 加仓次数 
add_ratio = 1.2   # 加仓倍数,每次加仓按此比例增加仓位
lots = 0.01         # 基础仓位,全局变量
login = 51216056 
password = "jjhot7xd"
server = "ICMarketsEU-Demo"
symbol = "EURUSD"     # 交易品种 
count = 30                 # 获取的K线根数  
timeframe = mt5.TIMEFRAME_D1       # 时间频率

tp = 0                          # 止盈点数,暂时设置为0       
sl = 0                          # 止损点数,暂时设置为0

magic = 10086    # 魔术数字,用于辨识订单
comment = "Bollinger bands"    # 订单注释   
deviation = 20                # 最大允许偏差值,订单执行时价格偏差范围 

def run_loop():
    while True:
        main()  # 调用主函数
        time.sleep(1)  # 延迟60秒,控制循环频率


def connect_to_mt5():
    """连接到MetaTrader 5"""
    try:
        # 初始化与MetaTrader 5程序端的连接
        mt5.initialize() 
        
        # 使用指定参数连接交易账户
        mt5.login(login, password, server) 
        
        # 获取账户信息
        account_info = mt5.account_info()
        if account_info is not None:
            print("登录成功!")
            print("账户信息:", account_info)
            return True
        else:
            print("无法获取账户信息!")
            return None
    except Exception as err:
        logger.error(err)  # 记录错误日志
        return None   # 返回None

def get_quote(symbol):
    """获取指定交易品种的报价"""
    tick_info = mt5.symbol_info_tick(symbol)
    if tick_info is None:
        print(symbol, "未找到报价")
        return None
    else:
        bid = round(tick_info.bid, 5)
        ask = round(tick_info.ask, 5)
        
        if bid == ask:
            price = bid
        else:
            price = round((bid + ask) / 2, 5)
        
        print(symbol, "Price:", price)
        return price


    
    
def get_bars():
    """获取当前K线的前N根K线"""
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count) 
        return rates
    except Exception as err:
        logger.error(err)  # 记录错误日志
        return None   # 返回None
    
    
def calculate_bollinger_bands():
    """计算布林带"""
    timeperiod = 20  
    nbdevup = 2  
    nbdevdn = 2  
    matype = MA_Type.SMA
    
    rates = get_bars()
    if rates is not None:
        close_prices = rates['close'][:-1] 

        upper, middle, lower = talib.BBANDS(close_prices,  
                                     timeperiod=timeperiod,  
                                     nbdevup=nbdevup,    
                                     nbdevdn=nbdevdn,   
                                     matype=matype) 

        upper = np.round(upper, 5)
        middle = np.round(middle, 5)
        lower = np.round(lower, 5)
        
        return upper, middle, lower
    else:
        print("无法获取K线数据")
        return None       
    
def extract_support_resistance(upper, lower):
    """提取支撑位和阻力位"""
    highs = np.round(np.nanmax(upper[-11:], axis=0), 5)
    lows = np.round(np.nanmin(lower[-11:], axis=0), 5)

    return highs, lows  

def calculate_points(highs, lows, price):
    """计算当前报价到支撑位和阻力位的点数"""
    points_to_support = round(price - lows, 5)
    points_to_resistance = round(highs - price, 5)
    
    return points_to_support, points_to_resistance

def execute_trade(points_to_support, points_to_resistance, min_gap, max_gap):
    """根据当前价格和支撑位、阻力位执行交易"""  

    # 判断是否开仓
    if min_gap <= points_to_support <= max_gap and min_gap <= points_to_resistance <= max_gap:
        if points_to_resistance < points_to_support:
            # 开多头仓位
            action = "buy"
            print("多头信号")
            order_type = mt5.ORDER_TYPE_BUY
        else:
            # 开空头仓位
            action = "sell"
            print("空头信号")
            order_type = mt5.ORDER_TYPE_SELL
            
    #下单请求
    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": order_type,  # 根据判断结果设置订单类型
        "price": 0.0,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "deviation": deviation
    }
    result = mt5.order_send(order_request)

    if result is None:
        print("下单请求发送失败")
        return  
      




# In[8]:


def main():
    # 连接到MetaTrader 5
    connect_to_mt5()


    # 获取K线数据
    bars = get_bars()
    print("获取到的K线数据:", bars)

    # 调用计算布林带函数
    bands = calculate_bollinger_bands()
    if bands is not None:
        upper, middle, lower = bands
        print("上轨:", upper)
        print("中轨:", middle)
        print("下轨:", lower)

    # 在调用calculate_bollinger_bands()后获取上轨、中轨和下轨
    upper, middle, lower = calculate_bollinger_bands()

    # 提取支撑位和阻力位
    highs, lows = extract_support_resistance(upper, lower)

    # 输出支撑位和阻力位
    print("支撑位:", lows)
    print("阻力位:", highs)

    # 调用函数获取报价
    price = get_quote(symbol)

    # 计算当前报价到支撑位和阻力位的点数
    points_to_support, points_to_resistance = calculate_points(highs, lows, price)

    print("到支撑位还有{}点".format(points_to_support))  
    print("到阻力位还有{}点".format(points_to_resistance))
    
     
    execute_trade(points_to_support, points_to_resistance, min_gap, max_gap)
        

if __name__ == "__main__":
    main()  # 首次调用主函数
    run_loop()  # 调用循环函数,开始循环
    
    


# In[ ]:





# In[ ]:





# In[ ]:




