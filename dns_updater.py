import requests
import os
import logging
import datetime

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
    
    for i in range(1,4):
        #logging.info((i-1)%3,colos[(i-1)%3],(i-1)//3,results[colos[(i-1)%3]][(i-1)//3])
        set_cloudflare_dns(DNS_RECORD_NAME=f"node{i}",CURRENT_IP=results[colos[(i-1)%3]][(i-1)//3])
        
    # 定义目标 URL
    url = "https://ipdb.api.030101.xyz/?type=bestcf"
    headers = {
        "Content-Type": "application/json"
    }
    # 发送 GET 请求
    response = requests.get(url, headers=headers)
    result = response.text
    results = result.strip().split('\n')
    logging.info(results)
    
    for i in range(4,7):
        set_cloudflare_dns(DNS_RECORD_NAME=f"node{i}",CURRENT_IP=results[(i-1)%3])
    
    logging.info('done')

def clean_workflows(REPO = "Hphscodehome/dns-updater",
                    TOKEN = os.getenv("TOKEN"),
                    DAYS_TO_KEEP = 2):
    BASE_URL = f"https://api.github.com/repos/{REPO}/actions/runs"
    HEADERS = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # 计算三天前的日期
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=DAYS_TO_KEEP)
    # 获取所有 Workflow 运行记录
    response = requests.get(BASE_URL, headers=HEADERS)
    
    logging.info(f"response: {response}")
    runs = response.json().get("workflow_runs", [])
    # 遍历并删除旧的运行记录
    for run in runs:
        run_date = datetime.datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if run_date < cutoff_date:
            run_id = run["id"]
            delete_url = f"{BASE_URL}/{run_id}"
            delete_response = requests.delete(delete_url, headers=HEADERS)
            if delete_response.status_code == 204:
                logging.info(f"成功删除 Workflow 运行记录 ID: {run_id}")
            else:
                logging.info(f"删除失败 ID: {run_id}, 状态码: {delete_response.status_code}")
                
    logging.info("清理完成！")
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    current_time = datetime.datetime.now()
    logging.info(f"current_time:{current_time}")
    get_ipv4()
    clean_workflows()