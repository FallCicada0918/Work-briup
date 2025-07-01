'''
Description: 
Author: FallCicada
Date: 2025-07-01 10:21:10
LastEditors: FallCicada
LastEditTime: 2025-07-01 10:24:38
Slogan: 無限進步
'''
import requests
import json
from urllib.parse import urlparse, parse_qs

class FeishuSheetsAPI:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
    
    def get_tenant_access_token(self):
        """获取tenant_access_token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload, proxies={'http': None, 'https': None})
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                return self.access_token
            else:
                print(f"获取token失败: {result}")
                return None
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
    
    def parse_sheet_url(self, sheet_url):
        """解析飞书表格URL，提取spreadsheet_token和sheet_id"""
        # URL示例: https://t1qnb0eyve9.feishu.cn/sheets/YMgds6AzWhoi7HtPHOhcpl42nph?sheet=Xq92uM
        
        # 提取spreadsheet_token (路径中sheets/后面的部分)
        path_parts = urlparse(sheet_url).path.split('/')
        spreadsheet_token = None
        for i, part in enumerate(path_parts):
            if part == 'sheets' and i + 1 < len(path_parts):
                spreadsheet_token = path_parts[i + 1]
                break
        
        # 提取sheet_id (查询参数中的sheet值)
        query_params = parse_qs(urlparse(sheet_url).query)
        sheet_id = query_params.get('sheet', [None])[0]
        
        return spreadsheet_token, sheet_id
    
    def get_sheet_meta_info(self, spreadsheet_token):
        """获取表格元信息"""
        if not self.access_token:
            print("请先获取access_token")
            return None
            
        url = f"{self.base_url}/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, proxies={'http': None, 'https': None})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"获取表格信息失败: {e}")
            return None
    
    def get_sheet_values(self, spreadsheet_token, sheet_id, value_range="A1:Z1000"):
        """获取表格数据"""
        if not self.access_token:
            print("请先获取access_token")
            return None
            
        # 构建查询参数
        params = {
            "valueRenderOption": "ToString",  # 格式化选项
            "dateTimeRenderOption": "FormattedString"  # 日期时间格式
        }
        
        url = f"{self.base_url}/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}!{value_range}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, proxies={'http': None, 'https': None})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"获取表格数据失败: {e}")
            return None
    
    def crawl_sheet_data(self, sheet_url, value_range="A1:Z1000"):
        """完整的爬取流程"""
        print("开始爬取飞书表格数据...")
        
        # 1. 获取访问令牌
        if not self.get_tenant_access_token():
            return None
        print("✓ 获取访问令牌成功")
        
        # 2. 解析URL
        spreadsheet_token, sheet_id = self.parse_sheet_url(sheet_url)
        if not spreadsheet_token:
            print("✗ 无法解析表格URL")
            return None
        print(f"✓ 解析URL成功 - spreadsheet_token: {spreadsheet_token}, sheet_id: {sheet_id}")
        
        # 3. 获取表格信息
        meta_info = self.get_sheet_meta_info(spreadsheet_token)
        if meta_info and meta_info.get("code") == 0:
            sheets = meta_info.get("data", {}).get("sheets", [])
            print(f"✓ 获取到 {len(sheets)} 个工作表")
            
            # 如果没有指定sheet_id，使用第一个工作表
            if not sheet_id and sheets:
                sheet_id = sheets[0].get("sheet_id")
                print(f"使用第一个工作表: {sheet_id}")
        
        # 4. 获取数据
        data = self.get_sheet_values(spreadsheet_token, sheet_id, value_range)
        if data and data.get("code") == 0:
            values = data.get("data", {}).get("values", [])
            print(f"✓ 成功获取数据，共 {len(values)} 行")
            return values
        else:
            print(f"✗ 获取数据失败: {data}")
            return None

# 使用示例
def main():
    # 配置你的应用信息
    APP_ID = input("请输入你的App ID: ")  # 替换为你的App ID
    APP_SECRET = input("请输入你的App Secret: ")  # 替换为你的App Secret
    
    # 你的表格URL
    SHEET_URL = "https://t1qnb0eyve9.feishu.cn/sheets/YMgds6AzWhoi7HtPHOhcpl42nph?sheet=Xq92uM"
    
    # 创建API客户端
    client = FeishuSheetsAPI(APP_ID, APP_SECRET)
    
    # 爬取数据
    data = client.crawl_sheet_data(SHEET_URL)
    
    if data:
        print("\n获取到的数据:")
        for i, row in enumerate(data[:5]):  # 只显示前5行
            print(f"第{i+1}行: {row}")
        
        # 保存到文件
        with open("feishu_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n数据已保存到 feishu_data.json")
    else:
        print("爬取失败")

if __name__ == "__main__":
    main()