# import requests
# import json

# url = "http://112.5.142.51:30080/api/bywin-guicang-knowledge/knowledge/authority/vector/retrieval"
# headers = {
#     "Content-Type": "application/json",
#     "APP_KEY": "850db3da393046e898cbc1b11b257286"
# }
# data = {
#     "knowledge_id": "1907015570507436034",
#     "query": "2022年南平武夷山35kV岚谷变10kV黎口线个支线改造工程的工程竣工决算合规性进行分析",
#     "retrieval_setting": {
#         "top_k": 5,
#         "score_threshold": 0.1
#     }
# }

# response = requests.post(url, headers=headers, data=json.dumps(data))
# print(response.json())

#-------------------

# import requests

# url = "http://112.5.142.51:30080/api/bywin-guicang-knowledge/knowledge/authority/resource/page"
# headers = {
#     "APP_KEY": "850db3da393046e898cbc1b11b257286"
# }
# params = {
#     "currentPage": 1,
#     "pageSize": 10,
#     "knowledgeId": "1907015570507436034",
#     "keyword": "搜索关键词",  # 可选
#     "type": 0  # 可选，0=文档 1=api 2=库表
# }

# response = requests.get(url, headers=headers, params=params)
# print(response.json())

#--------------------

# import requests
# import json

# url = "http://112.5.142.51:30080/api/bywin-guicang-knowledge/knowledge/authority/vector/retrieval"
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": "850db3da393046e898cbc1b11b257286"  # 直接使用APP_KEY
# }
# data = {
#     "knowledge_id": "1907015570507436034",
#     "query": "测试查询",
#     "retrieval_setting": {
#         "top_k": 5,
#         "score_threshold": 0.1
#     }
# }

# response = requests.post(url, headers=headers, data=json.dumps(data))
# print(response.json())

#----------------------

import requests

url = "http://112.5.142.51:30080/api/bywin-guicang-knowledge/knowledge/authority/knowledge/page"
headers = {
    "Authorization": "850db3da393046e898cbc1b11b257286"  # 直接使用APP_KEY
}

# 必选参数
params = {
    "currentPage": 1,           # 当前页
    "pageSize": 10,             # 页大小
    "knowledgeId": "1907015570507436034",  # 知识库ID
    "keyword": "2022年南平武夷山35kV岚谷变10kV黎口线个支线改造工程的工程竣工决算合规性进行分析"
}

response = requests.get(url, headers=headers, params=params)
print(response.json())