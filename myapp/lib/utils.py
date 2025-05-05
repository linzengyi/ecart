from datetime import datetime

def generate_order_number(counter: int) -> str:
    """
    產生 12 碼訂單號碼
    :param counter: 流水號 (從 1 開始)
    :return: 訂單號碼 (格式: YYYYX0000001)
    """
    year = datetime.now().year  # 取得當前年份
    month = datetime.now().month  # 取得當前月份
    
    # 10、11、12 月轉換為 A、B、C，其他月份取個位數
    month_code = str(month % 10) if month <= 9 else "ABC"[month - 10]
    
    # 格式化流水號，補 0 至 7 碼
    serial_number = f"{counter:07d}"
    
    # 組合訂單號碼
    return f"{year}{month_code}{serial_number}"
