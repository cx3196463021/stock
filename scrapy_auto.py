import requests
import json
from concurrent.futures import ThreadPoolExecutor

xls_xpath = 'Table.xls'

def get_industry_information(xls_xpath):
       industry_data = {}
       with open(xls_xpath, 'r', encoding='gbk') as f:
              lines = f.readlines()
              for line in lines[1:]:
                     line = line.strip()
                     informations = line.split()
                     if not informations:
                            continue
                     if informations:
                            information_code = informations[0]
                            information_code = information_code[:2].lower() + information_code[2:]
                            information_name = informations[1]
                            stock_industry = informations[2]
                            row_data = {
                                   "股票代码": information_code,
                                   "股票名称": information_name,
                                   "所属行业": stock_industry
                            }
                            if stock_industry not in industry_data:
                                   industry_data[stock_industry] = []
                            industry_data[stock_industry].append(row_data)
       print("按板块分类完毕：")
       for industry, stocks in industry_data.items():
              print(f"{industry}：{len(stocks)}只股票")

       return industry_data

def get_instant_data(stock_code):
       url = 'http://qt.gtimg.cn/q={stock_code}'
       headers = {
              'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0'
       }
       res = requests.get(url.format(stock_code=stock_code), headers=headers)
       content = res.text

       if '=' in content:
              real_content = content.split('=')[1].strip('";\n')
              result = real_content.split('~')

              stock_info = {
                     '股票代码': stock_code,
                     '股票名称': result[1],
                     '流通市值': result[44],
                     '成交额': result[37],
                     '换手率': result[38],
                     '当前价格': result[3],
                     '今日最高价': result[41],
                     '今日最低价': result[42],
                     '今日涨幅%': result[32],
                     '今日涨停价': result[47],
                     '今日跌停价': result[48],
              }
              print(f"返回股票最新数据：{stock_code}")
              print(stock_info)
              return stock_info
       else:
              print(f"返回股票最新数据时格式异常，无法解析：{stock_code}")
              return None

def process_single_stock(stock):
       stock_code = stock['股票代码']
       number_stock_code = stock_code[-6:]

       secid = None
       if number_stock_code.startswith(('600', '601', '603', '605', '688', '900')):
              secid = f"1.{number_stock_code}"
       elif number_stock_code.startswith(('000', '001', '002', '003', '300', '301', '200')):
              secid = f"0.{number_stock_code}"
       elif number_stock_code.startswith(('430', '8')):
              secid = f"2.{number_stock_code}"
       else:
              print(f"无法识别股票代码：{number_stock_code}")
              return None

       instant_info = get_instant_data(stock_code)
       if instant_info is None:
              return None

       try:
              url = f'https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?cb=jQuery112303483348048819973_1745814493732&lmt=0&klt=101&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&secid={secid}&_=1745814493733'
              res = requests.get(url, proxies={})  # 禁用代理，防止连不上
              text = res.text
              start = text.find('(') + 1
              end = text.rfind(')')
              json_data = json.loads(text[start:end])

              klines = json_data['data']['klines']
              if not klines or len(klines) < 30:
                     print(f"股票 {stock_code} 历史数据不足30条，跳过")
                     return None

              # 去除今天的数据
              historical_klines = klines[:-1]

              if len(historical_klines) < 30:
                     print(f"股票 {stock_code} 去除今天后历史数据不足30条，跳过")
                     return None

              # 5日最高最低（不包含今天）
              five_days_data = historical_klines[-5:]
              five_days_closing_price = [float(day.split(',')[-4]) for day in five_days_data]
              five_day_max = max(five_days_closing_price)
              five_day_min = min(five_days_closing_price)

              # 30日最高最低（不包含今天）
              thirty_days_data = historical_klines[-30:]
              thirty_days_closing_price = [float(day.split(',')[-4]) for day in thirty_days_data]
              thirty_day_max = max(thirty_days_closing_price)
              thirty_day_min = min(thirty_days_closing_price)

              stock_result = {
                     '股票代码': stock_code,
                     '股票名称': stock['股票名称'],
                     '所属行业': stock['所属行业'],
                     '5日最高收盘价': five_day_max,
                     '5日最低收盘价': five_day_min,
                     '30日最高收盘价': thirty_day_max,
                     '30日最低收盘价': thirty_day_min,
              }
              stock_result.update(instant_info)
              print(f"最新的数据{stock_result}")
              return stock_result

       except Exception as e:
              print(f"股票 {stock_code} 历史数据处理失败，原因：{e}")
              return None

def get_history_data(stock_list):
       all_stock_data = []
       with ThreadPoolExecutor(max_workers=200) as executor:
              futures = executor.map(process_single_stock, stock_list)
              for result in futures:
                     if result is not None:
                            all_stock_data.append(result)
       print("全部股票处理完成")
       return all_stock_data

def get_remaining_result(all_stock_data):
       result_list = []  # 创建一个列表，保存所有股票数据

       for stock in all_stock_data:
              current_price = float(stock['当前价格'])
              today_high_price = float(stock['今日最高价'])
              today_low_price = float(stock['今日最低价'])
              five_days_high_price = float(stock['5日最高收盘价'])
              five_days_low_price = float(stock['5日最低收盘价'])
              thirty_days_high_price = float(stock['30日最高收盘价'])
              thirty_days_low_price = float(stock['30日最低收盘价'])

              # 离今日最高
              if today_high_price != 0:
                     dist_today_high_pct = (current_price - today_high_price) / today_high_price * 100
              else:
                     dist_today_high_pct = None
              stock['距今日最高%'] = dist_today_high_pct

              # 离今日最低
              if today_low_price != 0:
                     dist_today_low_pct = (current_price - today_low_price) / today_low_price * 100
              else:
                     dist_today_low_pct = None
              stock['距今日最低%'] = dist_today_low_pct

              # 离5日最高
              if five_days_high_price != 0:
                     dist_five_days_high_pct = (current_price - five_days_high_price) / five_days_high_price * 100
              else:
                     dist_five_days_high_pct = None
              stock['距5日最高%'] = dist_five_days_high_pct

              # 离5日最低
              if five_days_low_price != 0:
                     dist_five_days_low_pct = (current_price - five_days_low_price) / five_days_low_price * 100
              else:
                     dist_five_days_low_pct = None
              stock['距5日最低%'] = dist_five_days_low_pct

              # 离30日最高
              if thirty_days_high_price != 0:
                     dist_thirty_days_high_pct = (current_price - thirty_days_high_price) / thirty_days_high_price * 100
              else:
                     dist_thirty_days_high_pct = None
              stock['距30日最高%'] = dist_thirty_days_high_pct

              # 离30日最低
              if thirty_days_low_price != 0:
                     dist_thirty_days_low_pct = (current_price - thirty_days_low_price) / thirty_days_low_price * 100
              else:
                     dist_thirty_days_low_pct = None
              stock['距30日最低%'] = dist_thirty_days_low_pct

              result_list.append(stock)
       print(f"全部的数据{result_list}")
       print(f"全部股票数据整理完成，共 {len(result_list)} 只股票")
       return result_list




if __name__ == '__main__':
       industry_stock_dict = get_industry_information(xls_xpath)

       # ======== 新增，让用户输入想查哪个行业 ========
       industry_name = input("请输入要查询的行业名称：").strip()

       if industry_name not in industry_stock_dict:
              print(f"行业【{industry_name}】不存在，请检查输入！")
       else:
              stocks = industry_stock_dict[industry_name]
              print(f"正在处理行业：{industry_name}，股票数：{len(stocks)}")
              all_stock_data = get_history_data(stocks)
              get_remaining_result(all_stock_data)
       get_remaining_result(all_stock_data)
