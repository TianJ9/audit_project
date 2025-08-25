import pandas as pd
from collections import defaultdict

# 读取Excel
file_path = "/Users/pantianjun/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_4wcxs40l6hy722_2acd/msg/file/2025-08/业数审汇总+案例数据20250822.xlsm"

class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child_node):
        if child_node not in self.children:
            self.children.append(child_node)

def build_tree(file_name):
    root = Node("root")
    level1_1 = Node("财务资产")
    root.add_child(level1_1)

    level2_a = Node("工程财务")
    level1_1.add_child(level2_a)

    level3_a1 = Node("建账建卡不规范")
    level3_a2 = Node("项目暂估转资及决算不规范")
    level3_a3 = Node("审定结算异常")
    level2_a.add_child(level3_a1)
    level2_a.add_child(level3_a2)
    level2_a.add_child(level3_a3)

    # level4_a1 = Node("资产分类异常")
    # level4_a2 = Node("1.工程未竣工提前暂估资产 2.暂估转资不及时")
    # level4_a3 = Node("审定结算不及时")
    # level4_a4 = Node("决算转资不及时")
    # level4_a5 = Node("资产价值与实际造价偏差大")
    # level3_a1.add_child(level4_a1)
    # level3_a2.add_child(level4_a2)
    # level3_a2.add_child(level4_a4)
    # level3_a2.add_child(level4_a5)
    # level3_a3.add_child(level4_a3)

    # risk_point1 = Node("资产卡片错、漏建")
    # risk_point2 = Node("预转资异常")
    # risk_point3 = Node("审定结算不及时")
    # risk_point4 = Node("正式转资异常")
    # risk_point5 = Node("资产价值与实际造价偏差大")
    
    # level4_a1.add_child(risk_point1)
    # level4_a2.add_child(risk_point2)
    # level4_a3.add_child(risk_point3)
    # level4_a4.add_child(risk_point4)
    # level4_a5.add_child(risk_point5)
    return root

from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

def model_gen(prompt):
    result = client.chat.completions.create(
        # model="deepseek/deepseek-r1-0528",
        model="deepseek/deepseek-chat-v3-0324",
        messages=[
            # {"role": "system", "content": "你是一个专业的审计专家，具备审计方向的背景知识，擅长分析各种审计项目并进行异常分析和排查。"},
            {"role": "user", "content": prompt}
        ],
        stream=False,
        temperature=0.0
    )
    response = result.choices[0].message.content
    return response

def tree_search(root,query):
    cur = root
    match_path = ""
    while cur is not None:
        if len(cur.children) == 0:
            break
        elif len(cur.children) == 1:
            match_path += cur.children[0].name
            match_path += " - "
            cur = cur.children[0]
        else:
            for item in cur.children:
                SYS_MSG = f'''请你判断当前给定的审计问题分类和用户输入的query是否有关，只需要输出“是”或者“不是”。审计问题分类：{item.name}。用户输入query：{query}'''
                result = model_gen(SYS_MSG).strip()
                if result == "是":
                    match_path += item.name
                    match_path += " - "
                    temp = item
            cur = temp
    match_path = match_path.strip().rstrip("-")
    return match_path
                
            
    
root = build_tree(file_path)
paths = tree_search(root,"转资异常分析")
print(paths)

@app.route('/api/ask_for_number', methods=['POST'])
def process_afn():
    data = request.get_json()
    risks = data.get("risks", [])
    output = run_pipelines(risks)
    return app.response_class(
        response=json.dumps({"result": output}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )