import requests
import os
import logging
from datetime import datetime

def set_cloudflare_dns(API_TOKEN = os.getenv("API_TOKEN"),
                       ZONE_ID = os.getenv("ZONE_ID"),
                       DNS_RECORD_NAME = "*",
                       DOMAIN = os.getenv("DOMAIN"),
                       CURRENT_IP = "*"):
    BASE_URL = "https://api.cloudflare.com/client/v4"
    HEADERS = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/zones/{ZONE_ID}/dns_records?name={DNS_RECORD_NAME}.{DOMAIN}"
    response = requests.get(url, headers=HEADERS)
    record_info = response.json()
    if not record_info["success"]:
        logging.info(f"获取 DNS 记录失败: {record_info['errors'][0]['message']}")
        return
    record_id = record_info["result"][0]["id"] if record_info["result"] else None
    dns_data = {
        "type": "A",
        "name": f"{DNS_RECORD_NAME}.{DOMAIN}",
        "content": CURRENT_IP,
        "ttl": 1,
        "proxied": False
    }
    if record_id is None:
        url = f"{BASE_URL}/zones/{ZONE_ID}/dns_records"
        response = requests.post(url, headers=HEADERS, json=dns_data)
    else:
        url = f"{BASE_URL}/zones/{ZONE_ID}/dns_records/{record_id}"
        response = requests.put(url, headers=HEADERS, json=dns_data)
    # 检查响应
    result = response.json()
    if result["success"]:
        logging.info(f"DNS 记录已更新为 {CURRENT_IP}")
    else:
        logging.info(f"更新 DNS 记录失败: {result['errors'][0]['message']}")
        
def get_ipv4():
    url = "https://api.hostmonit.com/get_optimization_ip"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "key": "o1zrmHAF",
        "type": "v4"
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    colos = ['CM','CT','CU']
    if result["code"] == 200:
        info = result["info"]
        results = {}
        for line_type, ip_list in info.items():
            if line_type in colos:
                for i,ip_info in enumerate(ip_list):
                    if i == 0:
                        results[line_type] = [ip_info['ip']]
                    else:
                        results[line_type].append(ip_info['ip'])
    else:
        logging.info(f"请求失败，状态码: {result['code']}")
    logging.info(results)
    for i in range(1,7):
        #logging.info((i-1)%3,colos[(i-1)%3],(i-1)//3,results[colos[(i-1)%3]][(i-1)//3])
        set_cloudflare_dns(DNS_RECORD_NAME=f"node{i}",CURRENT_IP=results[colos[(i-1)%3]][(i-1)//3])
    logging.info('done')
    
if __name__ == '__main__':
    current_time = datetime.now()
    logging.info(f"current_time:{current_time}")
    get_ipv4()