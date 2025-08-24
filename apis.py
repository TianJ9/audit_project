#Step 1 收到用户前端query，查询各种内容，得到异常排查方向
from flask import Flask, request, jsonify
import json

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

app = Flask(__name__)

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
    level3_to_risk_point = {
        "建账建卡不规范":[{
            "审计风险点":"资产卡片错、漏建",
            "审计风险描述":"对比项目资产级设备领用与已转资的资产卡片差异",
            "风险判定逻辑":"1.根据项目物资领用清单匹配“物料组与设备分类、资产分类”三码对应表，确定应建资产分类的资产卡片 2.与对项目转资明细的资产卡片的资产分类匹配差异，如果前者多则存在资产卡片漏建，如果前者少则存在错建资产卡片",
            "业务对象":"项目、物资、资产",
            "业财流程及活动":" 投运验收及预转资"
            }],
        "项目暂估转资及决算不规范":[{
            "审计风险点":"预转资异常",
            "审计风险描述":"对比项目投运日期和预转资日期，当预转资日期 >投运日期 + 30天，视为预转资超期，当预转资日期 <投运日期，视为预转资提前。",
            "风险判定逻辑":"1.预转资日期＞投运日期 2.预转资日期-投运日期＞30天",
            "业务对象":"项目",
            "业财流程及活动":" 投运验收及预转资"
            },
            {
            "审计风险点":"正式转资异常",
            "审计风险描述":"对比项目投运日期和竣工决算日期:1.项目类型为11，竣工决算日期>投运日期+360天 2.项目类型为13或15，竣工决算日期>投运日期+270天 3.其他资本性项目，竣工决算日期>投运日期+180天",
            "风险判定逻辑":"1.竣工决算日期-投运日期>360天 2.竣工决算日期-投运日期>270天 3.竣工决算日期-投运日期>180天",
            "业务对象":"项目",
            "业财流程及活动":" 投运验收及正式转资"
            },
            {
            "审计风险点":"资产价值与实际造价偏差大",
            "审计风险描述":"项目涉及的资产分摊价值 > 对应设备原始购置值*N倍",
            "风险判定逻辑":"资产转资金额/采购订单的设备购置价格>3倍",
            "业务对象":"项目、物资、资产",
            "业财流程及活动":" 投运验收及正式转资"
            }],
        "审定结算异常":[{
            "审计风险点":"审定结算不及时",
            "审计风险描述":"对比项目投运日期和工程结算日期:1.项目类型为11、13、15，工程结算日期>投运日期+100天 2.其他资本性项目，工程结算日期>投运日期+60天",
            "风险判定逻辑":"1.工程结算日期-投运日期>100天 2.工程结算日期-投运日期>60天",
            "业务对象":"项目",
            "业财流程及活动":" 工程建设（结算款）"
            }]
            }
    return root,level3_to_risk_point

def tree_search(root,query):
    cur = root
    match_path = ""
    while cur is not None:
        if len(cur.children) == 0:
            match_path = match_path.strip().rstrip("-")
            break
        elif len(cur.children) == 1:
            match_path += cur.children[0].name
            match_path += " - "
            cur = cur.children[0]
        else:
            for item in cur.children:
                SYS_MSG = f'''请你判断当前给定的审计问题分类和用户输入的query是否有关，只需要输出“是”或者“不是”。
                例如：
                审计问题分类：项目暂估转资及决算不规范。用户输入query：转资异常分析。输出：是
                审计问题分类：审定结算异常。用户输入query：转资异常分析。输出：不是

                下面给你分类和用户query：
                审计问题分类：{item.name}。用户输入query：{query}。输出'''
                result = model_gen(SYS_MSG).strip()
                if result == "是":
                    match_path += item.name
                    match_path += " - "
                    temp = item
            cur = temp
    match_path = match_path.strip().rstrip("-")
    return match_path

def thinking_process(query):
    # 你的逻辑
    SYS_MSG = '''请你针对用户输入的提问（一个审计问题），输出项目的内容范围（时间、是综合计划内的项目、是否是配网项目、项目的地点）。
下面是用户输入的提问：
'''
    model_thinking_content = model_gen(SYS_MSG + query)
    # "然后输出用户提问的业务对象是哪一个或哪几个（项目、物资、资产、设备），然后输出你对这个用户输入问题的问题定位，可能是哪些异常（从以下6个异常分类中选择单个或多个，不要解释：时间异常、金额异常、流程异常、资料异常、归类异常、状态异常）"

    SYS_MSG_1 = '''请你提取出用户输入的提问中，具体提问审计项目的什么方面，不要输出其他内容。例如：用户输入：对2022-2024年南平公司光泽县配网项目转资异常分析。输出：转资异常分析。
    下面是用户输入：'''
    analyse_point = model_gen(SYS_MSG_1 + query).strip()
    # print("analyse_point: ",analyse_point)

    root,level3_to_risk_point = build_tree("")
    paths = tree_search(root,analyse_point)
    level3 = paths.rsplit("-", 1)[-1].strip()
    risk_points_items = level3_to_risk_point[level3]

    risk_points = ""
    service_object = ""
    for i,item in enumerate(risk_points_items):
        if len(item["业务对象"])>len(service_object):
            service_object = item["业务对象"]
            # print("item[业务对象]: ",item["业务对象"])

        risk_points += f"{str(i+1)}. "
        risk_points += f'''{item["审计风险点"]}：{item["风险判定逻辑"]}\n'''
    
    # print("risk_points: ",risk_points)
    # print("service_object: ",service_object)
    model_thinking_content += f"\n用户提问的业务对象是:{service_object} \n"
    
    SYS_MSG_2 = f'''给你用户输入的问题，和判断得可能存在的风险点，请你从判断并选择该用户输入可能属于哪些异常，不要输出其他无关内容（从以下6个异常分类中选择单个或多个，不要解释：时间异常、金额异常、流程异常、资料异常、归类异常、状态异常）
    下面是用户输入的问题：{query}。
    判断得可能存在的风险点：{risk_points}。'''
    error_type = model_gen(SYS_MSG_2)

    model_thinking_content += f"\n对用户输入问题的问题定位为:\n{error_type}\n"

    model_thinking_content += f"从业数审图谱中推理得到路径：{paths}"
    # print(model_thinking_content)
    return model_thinking_content

def thinking_graph_output(error_type,reasoning_path):
    root,level3_to_risk_point = build_tree("")
    level3 = reasoning_path.rsplit("-", 1)[-1].strip()
    risk_points_items = level3_to_risk_point[level3]

    result_json = {"entities":[],"relationships":[]}
    SYS_MSG = '''请你抽取出所给文本中全部的异常分类，每行一个进行输出。
    下面是输入：'''
    error_extracted = model_gen(SYS_MSG+error_type).strip()
    errors = error_extracted.splitlines()

    for err in errors:
        result_json["entities"].append({"name":err.strip(),"type":"error_type"})
    for point in risk_points_items:
        has = False
        for item in result_json["entities"]:
            if item["name"]==point["业财流程及活动"].strip():
                has = True
                break
        if has is False:
            result_json["entities"].append({"name":point["业财流程及活动"].strip(),"type":"Processes and Activities"})
    for point in risk_points_items:
        result_json["entities"].append({"name":point["审计风险点"],"type":"risk_point"})
        result_json["relationships"].append({"from_entity":point['业财流程及活动'].strip(),"to_entity":point['审计风险点'],"relationship":"belongs_to"})

    for item_1 in result_json["entities"]:
        if item_1['type']=="error_type":
            for item_2 in result_json["entities"]:
                if item_2['type']=="Processes and Activities":
                    SYS_MSG_1 = f'''请你判断输入的异常类型和流程活动之间是否存在关联，存在则输出“是”，否则输出“否”，不要输出其他东西。
                    如输入的异常类型：时间异常，输入的流程活动：投运验收及预转资。两者之间存在关联，输出“是”
                    异常类型：{item_1['name']}。流程活动：{item_2['name']}。输出：'''
                    judge = model_gen(SYS_MSG_1)
                    if judge.strip()=="是":
                        result_json["relationships"].append({"from_entity":item_1['name'],"to_entity":item_2['name'],"relationship":"belongs_to"})
                    
    # print(result_json)
    return result_json


    
def check_steps_gen(data):
    # 你的逻辑
    temp_steps = '''
(1)项目清单范围确定：通过SQL脚本+API从数据中台获取2022至2024年度综合计划项目，筛选出南平公司光泽县公司负责的已竣工资本性投资项目清单。
(2)预转资异常排查：利用业数图谱推理出“工程投运日期、第一次转资日期”关键数据的来源，通过SQL脚本+API从数据中台相关数据，结合审计依据，根据逻辑推理的工程预转资异常判断规则，排查确定预转资提前或超期疑点。
(3)工程正式转资异常排查
(4)资产账面价值与实际造价不符排查
(5).....'''
    return temp_steps

def check_directions_gen(query):
    temp_json = {
    "entities": [
        {
            "name": "南平公司",
            "type": "Company"
        },
        {
            "name": "光泽县项目",
            "type": "Project"
        },
        {
            "name": "工程预转资异常",
            "type": "Issue"
        },
        {
            "name": "工程正式转资异常",
            "type": "Issue"
        },
        {
            "name": "资产账面价值与实际造价不符",
            "type": "Issue"
        }
    ],
    "relationships": [
        {
            "from_entity": "光泽县项目",
            "to_entity": "南平公司",
            "relationship": "belongs_to"
        },
        {
            "from_entity": "工程预转资异常",
            "to_entity": "光泽县项目",
            "relationship": "observed_in"
        },
        {
            "from_entity": "工程正式转资异常",
            "to_entity": "光泽县项目",
            "relationship": "observed_in"
        },
        {
            "from_entity": "资产账面价值与实际造价不符",
            "to_entity": "光泽县项目",
            "relationship": "observed_in"
        }
    ]
}
    return temp_json

def decision_logic_gen(check_direction):
    temp_logic = '''对比项目投运日期和预转资日期，当预转资日期 >投运日期 + 30天，视为预转资超期，当预转资日期 <投运日期，视为预转资提前。'''

    return temp_logic

def analyse_doubt_point(data):
    temp_query = '''进一步排查步骤
1、变更记录核查，查询投运日期是否存在变更记录。
2、投运日期真实性核查，系统投运日期与竣工验收报告的实际竣工日期是否一致。
3、投运日期真实性辅助核查，匹配物资到货/转储/领料、工作票记录、异动单的时间信息与系统投运日期的一致性。'''

    return temp_query

def analyse_root_reason(data):
    temp_query = '''根因分析：
    通过竣工验收报告、工单、物资流转等匹配稽核后，该配网项目实际投运日期为变更前的2022-12-23，且暂估转资日期2022-12-24，暂估转资合规，而投运日期变更为2023-05-06，晚于暂估转资，造成提前转资的假象。'''

    return temp_query

@app.route('/api/thinking_content', methods=['POST'])
def process_tc():
    data = request.get_json()
    query = data.get("query", "")
    result = thinking_process(query)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/api/thinking_graph', methods=['POST'])
def process_tg():
    data = request.get_json()
    error_type = data.get("error_type", "")
    reasoning_path = data.get("reasoning_path", "")
    result = thinking_graph_output(error_type,reasoning_path)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )


@app.route('/api/check_steps', methods=['POST'])
def process_1_2():
    data = request.get_json()
    result = check_steps_gen(data)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/api/check_directions', methods=['POST'])
def process_1_cd():
    data = request.get_json()
    query = data.get("query", "")
    result = check_directions_gen(query)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/api/decision_logic', methods=['POST'])
def process_1_dl():
    data = request.get_json()
    check_direction = data.get("check_direction", "")
    result = decision_logic_gen(check_direction)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/api/deepen_reasoning', methods=['POST'])
def process_2():
    data = request.get_json()
    result = analyse_doubt_point(data)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

@app.route('/api/root_reason_analyse', methods=['POST'])
def process_3():
    data = request.get_json()
    result = analyse_root_reason(data)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    # host=0.0.0.0 允许外部访问
    app.run(host='0.0.0.0', port=5000)
    # thinking_process("对2022-2024年南平公司光泽县配网项目转资异常分析")
    # thinking_graph_output("流程异常 资料异常 金额异常","财务资产 - 工程财务 - 项目暂估转资及决算不规范")

# curl -X POST https://d73631c3f7c9.ngrok-free.app/api/thinking_content \
#     -H "Content-Type: application/json" \
#     -d '{"query": "对2022-2024年南平公司光泽县配网项目转资异常分析"}'

# curl -X POST https://d73631c3f7c9.ngrok-free.app/api/thinking_graph \
#     -H "Content-Type: application/json" \
#     -d '{"error_type": "时间异常、金额异常","reasoning_path":"财务资产 - 工程财务 - 项目暂估转资及决算不规范"}'
