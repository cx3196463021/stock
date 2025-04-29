import webview
import os
import json
from scrapy_auto import get_industry_information, get_history_data, get_remaining_result

# 全局变量，用于存储股票的历史高低价和超越次数
stock_history = {}

# 修复Windows路径问题
path = r'F:\cipintongji\pachong4\.idea\src\Table.xls'

# 获取index.html的路径
base_path = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base_path, 'index.html')

# 添加数据加载检查
try:
    print(f"开始加载行业数据: {path}")
    industry_information = get_industry_information(path)

    # 检查数据是否成功加载
    if not industry_information:
        print("错误: 行业数据加载失败，没有获取到任何数据")
        import sys
        sys.exit(1)

    industry_names = list(industry_information.keys())
    print(f"行业数据加载成功，共 {len(industry_names)} 个行业")

    # 打印前10个行业作为检查
    print("前10个行业:", industry_names[:10])

    # 检查每个行业是否包含股票
    empty_industries = []
    for industry, stocks in industry_information.items():
        if not stocks:
            empty_industries.append(industry)

    if empty_industries:
        print(f"警告: 以下行业没有股票数据: {empty_industries}")

except Exception as e:
    print(f"错误: 加载行业数据失败: {e}")
    import sys
    sys.exit(1)

# 初始化股票历史数据存储
def init_stock_history(stocks):
    for stock in stocks:
        stock_code = stock['股票代码']
        if stock_code not in stock_history:
            stock_history[stock_code] = {
                'highest_today': float(stock['今日最高价']),
                'lowest_today': float(stock['今日最低价']),
                'highest_5day': float(stock['5日最高收盘价']),
                'lowest_5day': float(stock['5日最低收盘价']),
                'highest_30day': float(stock['30日最高收盘价']),
                'lowest_30day': float(stock['30日最低收盘价']),
                'count_today_high': 0,
                'count_today_low': 0,
                'count_5day_high': 0,
                'count_5day_low': 0,
                'count_30day_high': 0,
                'count_30day_low': 0
            }

# 更新股票价格和计数
def update_stock_counts(stocks):
    for stock in stocks:
        stock_code = stock['股票代码']
        current_price = float(stock['当前价格'])

        # 确保股票在历史记录中
        if stock_code not in stock_history:
            init_stock_history([stock])
            continue

        history = stock_history[stock_code]

        # 检查是否超越今日最高价
        if current_price > history['highest_today']:
            history['count_today_high'] += 1
            history['highest_today'] = current_price

        # 检查是否低于今日最低价
        if current_price < history['lowest_today']:
            history['count_today_low'] += 1
            history['lowest_today'] = current_price

        # 检查是否超越5日最高价
        if current_price > history['highest_5day']:
            history['count_5day_high'] += 1
            history['highest_5day'] = current_price

        # 检查是否低于5日最低价
        if current_price < history['lowest_5day']:
            history['count_5day_low'] += 1
            history['lowest_5day'] = current_price

        # 检查是否超越30日最高价
        if current_price > history['highest_30day']:
            history['count_30day_high'] += 1
            history['highest_30day'] = current_price

        # 检查是否低于30日最低价
        if current_price < history['lowest_30day']:
            history['count_30day_low'] += 1
            history['lowest_30day'] = current_price

        # 将计数添加到股票数据中
        stock['count_today_high'] = history['count_today_high']
        stock['count_today_low'] = history['count_today_low']
        stock['count_5day_high'] = history['count_5day_high']
        stock['count_5day_low'] = history['count_5day_low']
        stock['count_30day_high'] = history['count_30day_high']
        stock['count_30day_low'] = history['count_30day_low']

class Api:
    def __init__(self):
        # 将行业数据保存为实例属性
        self.industry_data = industry_information

    def get_industry_names(self):
        print("API方法被调用: get_industry_names")
        return industry_names

    def get_stock_information(self, industry_name):
        print(f"API方法被调用: get_stock_information - {industry_name}")

        # 检查行业是否存在
        if industry_name not in self.industry_data:
            print(f"行业【{industry_name}】不存在")
            return []

        # 获取该行业的股票列表
        stocks = self.industry_data[industry_name]

        # 检查股票数据
        if not stocks:
            print(f"行业【{industry_name}】没有股票数据")
            return []

        print(f"获取行业股票: {industry_name}，股票数: {len(stocks)}")

        # 如果需要详细信息，使用以下代码
        try:
            # 获取股票历史数据
            print(f"开始获取 {industry_name} 的历史数据...")
            all_stock_data = get_history_data(stocks)

            # 检查是否成功获取历史数据
            if not all_stock_data:
                print(f"警告: 未能获取 {industry_name} 的历史数据")
                return stocks

            print(f"成功获取历史数据，共 {len(all_stock_data)} 只股票")

            # 计算各项指标
            print(f"开始计算 {industry_name} 的指标数据...")
            result_list = get_remaining_result(all_stock_data)

            # 检查是否成功计算指标
            if not result_list:
                print(f"警告: 未能计算 {industry_name} 的指标数据")
                return all_stock_data

            print(f"成功获取 {industry_name} 的完整数据，共 {len(result_list)} 只股票")

            # 初始化股票历史数据（如果尚未初始化）
            init_stock_history(result_list)

            # 更新股票计数
            update_stock_counts(result_list)

            return result_list

        except Exception as e:
            print(f"获取股票数据发生错误: {e}")
            # 如果获取详细数据失败，返回基本信息
            return stocks

# 实例化Api对象
api = Api()

# 创建窗口
window = webview.create_window('股票爬取工具', html_path, js_api=api)

# 启动 Webview 应用
webview.start(debug=True)
