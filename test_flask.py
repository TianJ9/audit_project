import pandas as pd

def load_excel_data(file_path):
    """
    读取xlsm文件，第一行作为列名，从第二行开始读取数据
    
    Args:
        file_path (str): xlsm文件路径
        
    Returns:
        pandas.DataFrame: 数据框
    """
    data = pd.read_excel(file_path, engine='openpyxl', header=1)
    return data

def get_value_by_column_row(data, column_name, row_index):
    """
    根据列名和行索引获取值
    
    Args:
        data (pandas.DataFrame): 数据框
        column_name (str): 列名
        row_index (int): 行索引（从0开始）
        
    Returns:
        值或None
    """
    if column_name not in data.columns:
        return None
    if row_index >= len(data) or row_index < 0:
        return None
    return data.iloc[row_index][column_name]


# 使用示例
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "data", "业数审汇总+案例数据20250822.xlsm")
data = load_excel_data(file_path)

# 获取第0行"审计问题分类-一级"列的值
value = get_value_by_column_row(data, "业务对象", 7)
print("value: ",value)
