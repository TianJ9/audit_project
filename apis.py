#Step 1 收到用户前端query，查询各种内容，得到异常排查方向
from flask import Flask, request, jsonify, Response
import requests
import json
from Risk2SQL.infer_method import run_pipelines
from Summary import summary
from openai import OpenAI
#
# client = OpenAI(
#   base_url="https://openrouter.ai/api/v1",
#   api_key="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",
# )

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="sk-8d51d6ac51a54945a02d7979ef2e9e8f",
)
model="deepseek-chat"


def model_gen(prompt):
    result = client.chat.completions.create(
        # model="deepseek/deepseek-r1-0528",
        # model="deepseek/deepseek-chat-v3-0324",
        model=model,
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

@app.route('/api/stream', methods=['POST'])
def stream_chat():
    data = request.get_json()
    query = data.get("query", "")
    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [{"role": "user", "content": query}],
        "stream": True
    }
    base_url="https://openrouter.ai/api/v1/chat/completions"
    api_key="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"
    # 调用 openrouter，开启流式
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload["stream"] = True  # 确保流式

    r = requests.post(base_url, headers=headers, json=payload, stream=True)

    def generate():
        for chunk in r.iter_lines():
            if chunk:
                text = chunk.decode("utf-8")
                if text.startswith("data: "):
                    text = text[len("data: "):]
                if text == "[DONE]":
                    yield "[DONE]\n"
                    break
                try:
                    data = json.loads(text)
                    delta = data["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]
                except Exception as e:
                    print("解析出错:", e, text)

    return Response(generate(), mimetype="text/event-stream")

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
    project_scope = model_gen(SYS_MSG + query)
    model_thinking_content = project_scope
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
    return model_thinking_content, error_type, paths, project_scope

def thinking_process_v2(query):
    EXTRACT_MSG = '''请你提取出用户输入的提问中，具体提问审计项目的什么方面，不要输出其他内容。
    例如：用户输入：对2022-2024年南平公司光泽县配网项目转资异常分析。
    输出：转资异常分析。
    下面是用户输入：'''
    extracted_point = model_gen(EXTRACT_MSG + query).strip()
    print("extracted_point: ",extracted_point)

    PROJECT_SCOPE_MSG = '''请你针对用户输入的提问（一个审计问题），输出项目的内容范围（项目的组织、时间、一定是综合计划内的项目、是否是配网项目）。
    例如：
    用户输入：对2022-2024年南平公司光泽县配网项目转资异常分析
    输出：
    项目的组织是：南平公司光泽县
    项目的时间范围是：2022-2024年
    项目是综合计划内的项目
    项目是配网项目

下面是用户输入的提问：
'''
    project_scope = model_gen(PROJECT_SCOPE_MSG + query)

    #流程定位待定，假设拥有：投运及预转资、项目结算流程、决算及正式转资
    #分类得到待定，假设拥有：时间异常、金额异常、资产分类异常

    #通过流程定位+可能的之前步骤输入输出，得到绿色表的业财流程及活动
    Processes_activities = ["投运验收及预转资","工程建设（结算款）","投运验收及正式转资","工程物资采购及领用"]
    process_pos = "投运及预转资、项目结算流程、决算及正式转资"

    related_process_activities = []
    for item in Processes_activities:
        SELECT_MSG = f'''请你根据审计项目的待查问题以及项目的流程定位，判断项目是否和当前的业财流程及活动有关。有关则输出“是”，否则输出“否”，不输出其他无关内容。
        例如：
        项目待查问题：转资异常分析
        流程定位：投运及预转资、项目结算流程、决算及正式转资
        业财流程及活动：投运验收及预转资
        输出：是
        
        项目待查问题：{extracted_point}
        流程定位：{process_pos}
        业财流程及活动：{item}
        输出：
        '''
        related_or_not = model_gen(SELECT_MSG).strip()
        if related_or_not == "是":
            related_process_activities.append(item)
        
    #通过问题定位得到黄色表的4级分类
    level4_cls = ["资产分类异常","1.工程未竣工提前暂估资产 2.暂估转资不及时","审定结算不及时","决算转资不及时","资产价值与实际造价偏差大"]
    error_type = "时间异常、金额异常、资产分类异常"

    related_level4_cls = []
    for item in level4_cls:
        SELECT_MSG = f'''请你根据审计项目的判定得到的问题分类，判断该项目是否和当前的审计问题分类有关。有关则输出“是”，否则输出“否”，不输出其他无关内容。
        例如：
        问题分类：时间异常、金额异常、资产分类异常
        审计问题分类：1.工程未竣工提前暂估资产 2.暂估转资不及时
        输出：是
        
        问题分类：{error_type}
        审计问题分类：{item}
        输出：'''
        related_or_not = model_gen(SELECT_MSG).strip()
        if related_or_not == "是":
            related_level4_cls.append(item)
    
    ORGANIZE_MSG = f'''给你对一个审计项目的分析流程，请你按照给定的模版，组织内容，输出，使得看起来是一个整体性的分析思路。注意这是一个前置的分析报告。
    用户输入：{query}
    提取得到的用户问题点：{extracted_point}
    分析得到的项目范围：{project_scope}
    项目的异常流程定位：{process_pos}
    项目的异常问题分类：{error_type}
    可能属于的业财流程及活动：{', '.join(related_process_activities)}
    可能属于的审计问题分类：{', '.join(related_level4_cls)}

    输出模版：
    一、 背景与目的
    二、 主要异常方向
    三、 根本原因分析
    四、 潜在影响与风险

    请注意，可能属于的业财流程及活动，和可能属于的审计问题分类，需要原封不动地输出，不进行修改，后续需要提取他们
    '''
    # final_output = model_gen(ORGANIZE_MSG)
    # return final_output, error_type, project_scope
    return ORGANIZE_MSG


# def thinking_graph_output(error_type,reasoning_path):
#     root,level3_to_risk_point = build_tree("")
#     level3 = reasoning_path.rsplit("-", 1)[-1].strip()
#     risk_points_items = level3_to_risk_point[level3]

#     result_json = {"entities":[],"relationships":[]}
#     SYS_MSG = '''请你抽取出所给文本中全部的异常分类，每行一个进行输出。
#     下面是输入：'''
#     error_extracted = model_gen(SYS_MSG+error_type).strip()
#     errors = error_extracted.splitlines()

#     for err in errors:
#         result_json["entities"].append({"name":err.strip(),"type":"error_type"})
#     for point in risk_points_items:
#         has = False
#         for item in result_json["entities"]:
#             if item["name"]==point["业财流程及活动"].strip():
#                 has = True
#                 break
#         if has is False:
#             result_json["entities"].append({"name":point["业财流程及活动"].strip(),"type":"Processes and Activities"})
#     for point in risk_points_items:
#         result_json["entities"].append({"name":point["审计风险点"],"type":"risk_point"})
#         result_json["relationships"].append({"from_entity":point['业财流程及活动'].strip(),"to_entity":point['审计风险点'],"relationship":"belongs_to"})

#     for item_1 in result_json["entities"]:
#         if item_1['type']=="error_type":
#             for item_2 in result_json["entities"]:
#                 if item_2['type']=="Processes and Activities":
#                     SYS_MSG_1 = f'''请你判断输入的异常类型和流程活动之间是否存在关联，存在则输出“是”，否则输出“否”，不要输出其他东西。
#                     如输入的异常类型：时间异常，输入的流程活动：投运验收及预转资。两者之间存在关联，输出“是”
#                     异常类型：{item_1['name']}。流程活动：{item_2['name']}。输出：'''
#                     judge = model_gen(SYS_MSG_1)
#                     if judge.strip()=="是":
#                         result_json["relationships"].append({"from_entity":item_1['name'],"to_entity":item_2['name'],"relationship":"belongs_to"})
                    
#     # print(result_json)
#     return result_json

def thinking_graph_output_v2(content):
    MSG_1 = f'''请你抽取出这个回复中提到的可能的业财流程及活动，只输出抽取出的内容，不要输出其他东西

    例如：
    回复：
    # 2022-2024年南平公司光泽县配网项目转资异常分析报告

## 一、背景与目的

本报告针对2022-2024年期间南平公司光泽县配网项目的转资异常情况进行前置分析。作为综合计划内的配网建设项目，该项目在投运及预转资、项目结算流程、决算及正式转资等关键环节出现了异常情况。本分析旨在识别异常类型、定位问题根源、评估潜在风险，为后续详细审计工作提供方向性指导。

## 二、主要异常方向

通过对项目数据的初步梳理，发现以下三类主要异常：

1. **时间异常**：转资流程时间节点不符合规定要求
2. **金额异常**：转资金额与实际造价存在显著偏差
3. **资产分类异常**：资产归类不准确或不符合规范

## 三、根本原因分析

初步判断异常主要集中在以下业财流程及活动：
- 投运验收及预转资
- 投运验收及正式转资

可能涉及的审计问题分类包括：
- 资产分类异常
- 1.工程未竣工提前暂估资产
- 2.暂估转资不及时
- 决算转资不及时
- 资产价值与实际造价偏差大

## 四、潜在影响与风险

1. **财务报告风险**：转资异常可能导致资产价值反映不准确，影响财务报表可靠性
2. **资产管理风险**：资产分类不当会影响后续折旧计提和资产管理效率
3. **合规性风险**：不及时或不规范的转资操作可能违反相关财务和资产管理规定
4. **税务风险**：资产价值确认不准确可能导致税务申报偏差
5. **运营效率风险**：转资流程异常可能延误项目闭环，影响后续项目资金安排[DONE]

    业财流程及活动：
    - 投运验收及预转资
    - 投运验收及正式转资

    回复：{content}
    业财流程及活动：
    '''
    process_acc = model_gen(MSG_1).strip()
    print("process_acc. ",process_acc)

    MSG_2 = f'''请你抽取出这个回复中提到的可能的审计问题分类，只输出抽取出的内容，不要输出其他东西

        例如：
    回复：
    # 2022-2024年南平公司光泽县配网项目转资异常分析报告

## 一、背景与目的

本报告针对2022-2024年期间南平公司光泽县配网项目的转资异常情况进行前置分析。作为综合计划内的配网建设项目，该项目在投运及预转资、项目结算流程、决算及正式转资等关键环节出现了异常情况。本分析旨在识别异常类型、定位问题根源、评估潜在风险，为后续详细审计工作提供方向性指导。

## 二、主要异常方向

通过对项目数据的初步梳理，发现以下三类主要异常：

1. **时间异常**：转资流程时间节点不符合规定要求
2. **金额异常**：转资金额与实际造价存在显著偏差
3. **资产分类异常**：资产归类不准确或不符合规范

## 三、根本原因分析

初步判断异常主要集中在以下业财流程及活动：
- 投运验收及预转资
- 投运验收及正式转资

可能涉及的审计问题分类包括：
- 资产分类异常
- 1.工程未竣工提前暂估资产
- 2.暂估转资不及时
- 决算转资不及时
- 资产价值与实际造价偏差大

## 四、潜在影响与风险

1. **财务报告风险**：转资异常可能导致资产价值反映不准确，影响财务报表可靠性
2. **资产管理风险**：资产分类不当会影响后续折旧计提和资产管理效率
3. **合规性风险**：不及时或不规范的转资操作可能违反相关财务和资产管理规定
4. **税务风险**：资产价值确认不准确可能导致税务申报偏差
5. **运营效率风险**：转资流程异常可能延误项目闭环，影响后续项目资金安排[DONE]

    审计问题分类：
- 资产分类异常
- 1.工程未竣工提前暂估资产
- 2.暂估转资不及时
- 决算转资不及时
- 资产价值与实际造价偏差大

    回复：{content}
    审计问题分类：
    '''
    risk_point_cls = model_gen(MSG_2).strip()
    print("risk_point_cls. ",risk_point_cls)

    risk_list = ["资产卡片错、漏建","预转资异常","审定结算不及时","正式转资异常","资产价值与实际造价偏差大","竣工工期异常","物资消耗异常"]
    risk_mapping = {"资产卡片错、漏建":{
        "政策制度及管理办法":"《国网运检部关于印发电网生产设备分类和固定资产目录对应关系的通知》(运检计划〔2013〕547号)要求，创建相关资产卡片。",
        "风险判定逻辑":"1.根据项目物资领用清单匹配“物料组与设备分类、资产分类”三码对应表，确定应建资产分类的资产卡片 2.与对项目转资明细的资产卡片的资产分类匹配差异，如果前者多则存在资产卡片漏建，如果前者少则存在错建资产卡片",
        "流程节点":"设备验收清单审批流程经实物管理部门审批通过后，提交财务部审批后生成资产编码，生成资产卡片（无资产价值、入账时间）",
        "业务对象":"项目、物资、资产"
        },
        "预转资异常":{
        "政策制度及管理办法":"《国家电网有限公司工程财务管理办法（2023）》第六章第三十四（二）规定“原则上应在投产后30日内完成工程暂估预转资手续，并及时准确计提折旧费用，折旧计提起始时间为竣工投运后的次月。”",
        "风险判定逻辑":"1.预转资日期＞投运日期 2.预转资日期-投运日期＞30天",
        "流程节点":"财务部核对ERP系统自动获取的设备资产购置价值，分摊工程费用后，形成固定资产卡片",
        "业务对象":"项目"
        },
        "审定结算不及时":{
        "政策制度及管理办法":"《国家电网有限公司工程财务管理办法（2023）》第七章第四十五（二）规定：1.特高压工程及抽水蓄能项目在竣工投运后 100 日内完成 工程结算编制和审核，财务部门在收到工程结算资料后 260 日内完成竣工决算报告编制。工程竣工决算整体时间原则上控制在工 程竣工投运后 1 年内完成。2.220 千伏及以上至 750 千伏电网基建工程在竣工投运后 100 日内完成工程结算编制和审核，财务部门在收到结算资料后 170 日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 9 个月内完成。3.110 千伏及以下电网基建工程、生产技术改造项目、电网小型基建、电力市场营销、电网数字化等其他工程在竣工投运后60日内完成工程结算编制和审核，财务部门在收到结算资料后120日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 6个月内完成。",
        "风险判定逻辑":"1.工程结算日期-投运日期>100天 2.工程结算日期-投运日期>60天",
        "流程节点":"工程竣工后，根据审核单位出具的工程结算审核征询意见书、开工报告、竣工报告、农民工工资承诺书、《支付施工尾款确认表》办理结算款",
        "业务对象":"项目"
        },
        "正式转资异常":{
        "政策制度及管理办法":"《国家电网有限公司工程财务管理办法（2023）》第七章第四十五（二）规定：1.特高压工程及抽水蓄能项目在竣工投运后 100 日内完成 工程结算编制和审核，财务部门在收到工程结算资料后 260 日内完成竣工决算报告编制。工程竣工决算整体时间原则上控制在工 程竣工投运后 1 年内完成。2.220 千伏及以上至 750 千伏电网基建工程在竣工投运后 100 日内完成工程结算编制和审核，财务部门在收到结算资料后 170 日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 9 个月内完成。3.110 千伏及以下电网基建工程、生产技术改造项目、电网小型基建、电力市场营销、电网数字化等其他工程在竣工投运后60日内完成工程结算编制和审核，财务部门在收到结算资料后120日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 6个月内完成。",
        "风险判定逻辑":"1.竣工决算日期-投运日期>360天 2.竣工决算日期-投运日期>270天 3.竣工决算日期-投运日期>180天",
        "流程节点":"财务部核对ERP系统自动获取的设备资产购置价值，分摊工程费用后，形成完善的固定资产卡片，完成在建工程转固定资产流程",
        "业务对象":"项目"
        },
        "资产价值与实际造价偏差大":{
        "政策制度及管理办法":"",
        "风险判定逻辑":"资产转资金额/采购订单的设备购置价格>3倍",
        "流程节点":"财务部核对ERP系统自动获取的设备资产购置价值，分摊工程费用后，形成完善的固定资产卡片，完成在建工程转固定资产流程",
        "业务对象":"项目、物资、资产"
        },
        "竣工工期异常":{
        "政策制度及管理办法":"《国家电网有限公司审计问题分类库（2025年版）》第1874条建设程序倒置具有相关特征，实际设备投运时间早于工程开工时间或晚于工程竣工竣工时间，关联转储工程采购的高价值设备物资与需求计划不匹配，可能存在刻意隐藏工程虚假异动关联的行为。",
        "风险判定逻辑":"1.竣工验收报告≠投运日期 2.异动单的实际完工日期>投运日期 3.物资发货日期>投运日期 4.物资收货日期>投运日期",
        "流程节点":"项目管理部门组织现场验收，非配网工程在ERP系统上传竣工验收报告，维护竣工日期;配网工程在配网工程全过程管控系统上传竣工验收报告，经审批后维护竣工日期，确认资产达到可使用状态",
        "业务对象":"项目、物资、设备"
        },
        "物资消耗异常":{
        "政策制度及管理办法":"《国家电网有限公司审计问题分类库（2025年版）》第1284条存在虚假出入库、频繁领退料具有相关特征，高退库率现象突出，转储物资与工程需求计划存在显著不匹配。",
        "风险判定逻辑":"1.项目物资采购申请数量>物资发货数量 2.项目物资收货数量>物资发货数量 3.项目物资储备数量≠领用数量",
        "流程节点":"1.项目管理部门根据项目立项时创建的预留号和wbs号/项目编码在erp系统发起采购需求，经审批提交协同办公系统，完成审批后上报招标需求，根据招投标结果签订合同 2.5物资部门根据领料申请单对物料领用出库记账，生成《物资出库单》",
        "业务对象":"项目、物资"
        }}
    related_risk_point = []
    for item in risk_list:
        SYS_MSG = f'''请你根据一个项目对应的一个风险的审计风险点分类，和对应的业财流程及活动，去判断下面风险点是否是对应的，是则输出“是”，否则输出“否”，不输出其他内容
        审计风险点分类:{risk_point_cls}
        业财流程及活动:{process_acc}
        风险点：{item}
        输出：'''
        judge = model_gen(SYS_MSG).strip()

        if judge == "是":
            related_risk_point.append(item)
    
    result_json = {"entities":[],"relationships":[]}
    for item in related_risk_point:
        result_json["entities"].append({"name":item,"type":"risk_point"})
        result_json["entities"].append({"name":risk_mapping[item]['政策制度及管理办法'],"type":"grounds"})
        result_json["entities"].append({"name":risk_mapping[item]['风险判定逻辑'],"type":"logic"})
        result_json["entities"].append({"name":risk_mapping[item]['流程节点'],"type":"process_item"})
        result_json["entities"].append({"name":risk_mapping[item]['业务对象'],"type":"service_object"})

        result_json["relationships"].append({"from_entity":item,"to_entity":risk_mapping[item]['政策制度及管理办法'],"relationship":"belongs_to"})
        result_json["relationships"].append({"from_entity":item,"to_entity":risk_mapping[item]['风险判定逻辑'],"relationship":"belongs_to"})
        result_json["relationships"].append({"from_entity":item,"to_entity":risk_mapping[item]['流程节点'],"relationship":"belongs_to"})
        result_json["relationships"].append({"from_entity":item,"to_entity":risk_mapping[item]['业务对象'],"relationship":"belongs_to"})
    return result_json

        

# API 1
@app.route('/api/thinking_content', methods=['POST'])
def process_tc():
    data = request.get_json()
    query = data.get("query", "")
    MSG = thinking_process_v2(query)

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [{"role": "user", "content": MSG}],
        "stream": True
    }
    base_url="https://openrouter.ai/api/v1/chat/completions"
    api_key="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"
    # 调用 openrouter，开启流式
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload["stream"] = True  # 确保流式

    r = requests.post(base_url, headers=headers, json=payload, stream=True)

    def generate():
        for chunk in r.iter_lines():
            if chunk:
                text = chunk.decode("utf-8")
                if text.startswith("data: "):
                    text = text[len("data: "):]
                if text == "[DONE]":
                    yield "[DONE]\n"
                    break
                try:
                    data = json.loads(text)
                    delta = data["choices"][0]["delta"]
                    if "content" in delta:
                        # yield delta["content"]
                        yield f'''data: {delta["content"]}\n\n'''
                        # yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"
                except Exception as e:
                    print("解析出错:", e, text)
    
    return Response(generate(), mimetype="text/event-stream")

# API 2
@app.route('/api/thinking_graph', methods=['POST'])
def process_tg():
    data = request.get_json()
    # 可能属于的业财流程及活动，和可能属于的审计问题分类
    # risk_point_cls = data.get("risk_point_cls", "")
    # process_acc = data.get("process_acc", "")
    content = data.get("content", "")
    result = thinking_graph_output_v2(content)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# API 3
@app.route('/api/ask_for_number', methods=['POST'])
def process_afn():
    data = request.get_json()
    risks = data.get("risks", [])
    output, graph = run_pipelines(risks)
    return app.response_class(
        # response=json.dumps({"result": {"output": output, "think_graph": graph}}, ensure_ascii=False),
        response=json.dumps({"result": output}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# API 4
@app.route('/api/task_plan', methods=['POST'])
def process_tp():
    data = request.get_json()

    process_type = data.get("process_type", "")
    problem_type = data.get("problem_type", "")
    project_scope = data.get("project_scope", "")
    problem_type_mapping = data.get("problem_type_mapping", "")
    risks = data.get("risks", [])
    risk_grounds = data.get("risk_grounds", [])
    logic = data.get("logic", "")
    process_item = data.get("process_item", "")
    service_object = data.get("service_object", "")
    risk2method = data.get("risk2method", "")
    sql = data.get("sql", "")

    result = summary.summary_Method(process_type, problem_type, project_scope, problem_type_mapping, risks, risk_grounds
                                    , logic, process_item, service_object, risk2method, sql)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# 过往作废api⬇
# @app.route('/api/check_steps', methods=['POST'])
# def process_1_2():
#     data = request.get_json()
#     result = check_steps_gen(data)
#     return app.response_class(
#         response=json.dumps({"result": result}, ensure_ascii=False),
#         status=200,
#         mimetype='application/json'
#     )

# @app.route('/api/check_directions', methods=['POST'])
# def process_1_cd():
#     data = request.get_json()
#     query = data.get("query", "")
#     result = check_directions_gen(query)
#     return app.response_class(
#         response=json.dumps({"result": result}, ensure_ascii=False),
#         status=200,
#         mimetype='application/json'
#     )

# @app.route('/api/decision_logic', methods=['POST'])
# def process_1_dl():
#     data = request.get_json()
#     check_direction = data.get("check_direction", "")
#     result = decision_logic_gen(check_direction)
#     return app.response_class(
#         response=json.dumps({"result": result}, ensure_ascii=False),
#         status=200,
#         mimetype='application/json'
#     )

# @app.route('/api/deepen_reasoning', methods=['POST'])
# def process_2():
#     data = request.get_json()
#     result = analyse_doubt_point(data)
#     return app.response_class(
#         response=json.dumps({"result": result}, ensure_ascii=False),
#         status=200,
#         mimetype='application/json'
#     )

# @app.route('/api/root_reason_analyse', methods=['POST'])
# def process_3():
#     data = request.get_json()
#     result = analyse_root_reason(data)
#     return app.response_class(
#         response=json.dumps({"result": result}, ensure_ascii=False),
#         status=200,
#         mimetype='application/json'
#     )

if __name__ == '__main__':
    # host=0.0.0.0 允许外部访问
    app.run(host='0.0.0.0', port=5000)
    # content = '''# 2022-2024年南平公司光泽县配网项目转资异常分析报告

# 调试代码，每次启动ngrok变换地址即可
# curl -X POST https://a51e2641775f.ngrok-free.app/api/ask_for_number \
#     -H "Content-Type: application/json" \
#     -d '{"risks": ["预转资异常","审定结算不及时"]}'

# curl -X POST https://867d4eea66dd.ngrok-free.app/api/thinking_graph \
#     -H "Content-Type: application/json" \
#     -d '{"risk_point_cls": "1.工程未竣工提前暂估资产 2.暂估转资不及时 审定结算不及时 资产价值与实际造价偏差大","process_acc":"投运验收及预转资 工程建设（结算款） 投运验收及正式转资"}'

# curl -X POST https://8b2f80d30fe8.ngrok-free.app/api/thinking_content \
#     -H "Content-Type: application/json" \
#     -d '{"query": "对2022-2024年南平公司光泽县配网项目转资异常分析"}'

# curl -X POST https://127.0.0.1:5001/api/thinking_content \
#     -H "Content-Type: application/json" \
#     -d '{"query": "对2022-2024年南平公司光泽县配网项目转资异常分析"}'

# curl -X POST https://8b2f80d30fe8.ngrok-free.app/api/thinking_graph \
#   -H "Content-Type: application/json" \
#   -d '{"content":"# 2022-2024年南平公司光泽县配网项目转资异常分析报告\n\n## 一、背景与目的\n\n本次分析针对南平公司光泽县2022-2024年综合计划内的配网项目转资异常情况。转资作为项目财务管理的关键环节，直接关系到资产计价准确性和财务数据真实性。通过对转资异常的系统性分析，旨在识别流程中的薄弱环节，揭示潜在的管理问题，为后续审计工作提供精准方向，同时促进企业规范项目管理、提升资产质量。\n\n## 二、主要异常方向\n\n本项目转资异常主要体现在以下三个维度：\n\n**时间异常**：包括投运预转资时点与项目进度不匹配、决算转资不及时等问题\n\n**金额异常**：表现为资产暂估价值与实际造价存在显著偏差\n\n**资产分类异常**：涉及资产科目归集不准确、分类标准执行不一致等情况\n\n## 三、根本原因分析\n\n### 流程定位分析\n主要异常集中在以下关键流程环节：\n- **投运及预转资流程**\n- **项目结算流程**\n- **决算及正式转资流程**\n\n### 具体问题表现\n*可能属于的业财流程及活动*：\n投运验收及预转资, 投运验收及正式转资\n\n*可能属于的审计问题分类*：\n1. 工程未竣工提前暂估资产\n2. 暂估转资不及时\n3. 决算转资不及时\n4. 资产价值与实际造价偏差大\n5. 资产分类异常\n\n### 成因追溯\n1. **前端管控不足**：项目进度管理粗放，导致预转资时点与工程实际完工进度脱节\n2. **过程监控缺失**：缺乏有效的动态成本管控机制，造成暂估价与最终决算差异较大\n3. **协同机制失效**：财务与业务部门信息不对称，转资所需的竣工资料传递延迟\n4. **标准执行偏差**：资产分类规则理解不一致，存在人为判断差异\n\n## 四、潜在影响与风险\n\n1. **财务报告风险**：导致资产负债表资产项失真，影响报表公允性\n2. **折旧计提偏差**：转资延迟或金额不准确将导致折旧计提错误\n3. **税务合规风险**：资产入账时点及价值不准确可能引发税务认定问题\n4. **管理决策误导**：失真的资产数据可能影响投资决策和资源配置\n5. **审计整改压力**：持续存在的转资异常可能引发监管关注和审计意见\n\n后续建议针对识别出的异常点和风险领域展开专项审计，重点验证流程合规性和数据真实性，同时建立跨部门的转资协同机制和预警体系。"}'

# curl -X POST https://a51e2641775f.ngrok-free.app/api/task_plan \
#   -H "Content-Type: application/json" \
#   -d '{"project_scope": "xxxx","risk2method": [{"风险点": "预转资异常", "审计风险描述": "对比项目投运日期和预转资日期，当预转资日期 >投运日期 + 30天，视为预转资超期，当预转资日期 <投运日期，视为预转资提前。", "政策制度及管理办法": "《国家电网有限公司工程财务管理办法（2023）》第六章第三十四（二）规定“原则上应在投产后30日内完成工程暂估预转资手续，并及时准确计提折旧费用，折旧计提起始时间为竣工投运后的次月。”", "风险判定逻辑": "1.预转资日期＞投运日期\n2.预转资日期-投运日期＞30天", "比对字段": ["预转资日期", "投运日期", "预转资日期", "投运日期"], "SQL": "根据您提供的需求，我将编写一个只返回投运日期的SQL脚本：\n\n```sql\nSELECT  prps.usr08 AS operation_start_date    -- 投运日期\nFROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj\nLEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS\nON      PROJ.PSPNR = prps.PSPHI  -- 外键关联(内码)\nAND     LENGTH(TRIM(PRPS.PSPNR)) > 0\nAND     prps.stufe IN (1, 2)\nAND     PRPS.mandt = '880'\nAND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')\nLEFT JOIN (\n            SELECT  prj_code\n                    ,COUNT(DISTINCT single_prj_code_14) AS NUM    -- 差异数\n            FROM    (\n                        SELECT  DISTINCT proj.pspid AS prj_code    -- 项目编码\n                                ,substr(prps.posid, 1, 14) single_prj_code_14    -- 前14位\n                        FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj\n                        LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS\n                        ON      PROJ.PSPNR = prps.PSPHI\n                        AND     LENGTH(TRIM(PRPS.PSPNR)) > 0\n                        AND     prps.stufe IN (1, 2)\n                        AND     PRPS.mandt = '880'\n                        AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')\n                        WHERE   proj.mandt = '880'\n                        AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')\n                    ) \n            GROUP BY prj_code\n        ) mid_tmp_filter_table\nON      mid_tmp_filter_table.prj_code = proj.pspid\nWHERE   proj.mandt = '880'\nAND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')\nAND     CASE WHEN mid_tmp_filter_table.NUM == 1 THEN prps.stufe = 1 ELSE prps.stufe = 2 END\nAND     proj.pspid in \n('18138721004F', '18138721004B', '18138721000U')\n;\n```\n\n这个脚本简化了原脚本，只返回投运日期(usr08)字段，同时保留了必要的关联条件和过滤逻辑。"}, {"风险点": "审定结算不及时", "审计风险描述": "对比项目投运日期和工程结算日期:\n1.项目类型为11、13、15，工程结算日期>投运日期+100天\n2.其他资本性项目，工程结算日期>投运日期+60天", "政策制度及管理办法": "《国家电网有限公司工程财务管理办法（2023）》第七章第四十五（二）规定：1.特高压工程及抽水蓄能项目在竣工投运后 100 日内完成 工程结算编制和审核，财务部门在收到工程结算资料后 260 日内完成竣工决算报告编制。工程竣工决算整体时间原则上控制在工 程竣工投运后 1 年内完成。2.220 千伏及以上至 750 千伏电网基建工程在竣工投运后 100 日内完成工程结算编制和审核，财务部门在收到结算资料后 170 日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 9 个月内完成。3.110 千伏及以下电网基建工程、生产技术改造项目、电网小型基建、电力市场营销、电网数字化等其他工程在竣工投运后60日内完成工程结算编制和审核，财务部门在收到结算资料后120日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 6个月内完成。", "风险判定逻辑": "1.工程结算日期-投运日期>100天\n2.工程结算日期-投运日期>60天", "比对字段": ["工程结算日期", "投运日期"], "SQL": "```sql\nSELECT  *\nFROM    (\n            SELECT  proj.pspid AS PSPID    -- 项目编码\n                    ,proj.post1 AS POST1    -- 描述\n                    ,proj.prctr AS PRCTR    -- 利润中心\n                    ,proj.vbukr AS VBUKR    -- 公司代码\n                    ,proj.vernr AS VERNR    -- 负责人编码\n                    ,prps.posid AS POSID    -- 单体工程编码\n                    ,prps.post1 AS PRPS_POST1    -- 描述\n                    ,prps.stufe AS STUFE    -- 层级\n                    ,prps.prart AS PRART    -- 类型\n                    ,prps.usr08 AS USR08    -- 投运日期\n                    ,prps.objnr AS OBJNR    -- 对象号\n                    ,prps.pspnr AS PSPNR    -- WBS内码\n                    ,prps.zgcjsrq AS ZGCJSRQ    -- 工程结算日期\n                    ,prps.zgjsrq AS ZJGJSRQ    -- 竣工决算日期\n                    ,ROW_NUMBER() OVER(PARTITION BY proj.pspid, proj.post1, proj.prctr, proj.vbukr, proj.vernr, \n                                      prps.posid, prps.post1, prps.stufe, prps.prart, prps.usr08, \n                                      prps.objnr, prps.pspnr, prps.zgcjsrq, prps.zgjsrq \n                                      ORDER BY prps.usr08) row_index\n            FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj\n            LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS\n            ON      PROJ.PSPNR = prps.PSPHI  -- 外检关联(内码)\n            AND     LENGTH(TRIM(PRPS.PSPNR)) > 0\n            AND     PRPS.mandt = '880'\n            AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')\n            WHERE   proj.mandt = '880'\n            AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')\n            AND     proj.pspid in \n            ('18138721004F', '18138721004B', '18138721000U')  \n        ) \nWHERE   row_index = 1\n;\n```"}, {"风险点": "审定结算不及时", "审计风险描述": "对比项目投运日期和工程结算日期:\n1.项目类型为11、13、15，工程结算日期>投运日期+100天\n2.其他资本性项目，工程结算日期>投运日期+60天", "政策制度及管理办法": "《国家电网有限公司工程财务管理办法（2023）》第七章第四十五（二）规定：1.特高压工程及抽水蓄能项目在竣工投运后 100 日内完成 工程结算编制和审核，财务部门在收到工程结算资料后 260 日内完成竣工决算报告编制。工程竣工决算整体时间原则上控制在工 程竣工投运后 1 年内完成。2.220 千伏及以上至 750 千伏电网基建工程在竣工投运后 100 日内完成工程结算编制和审核，财务部门在收到结算资料后 170 日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 9 个月内完成。3.110 千伏及以下电网基建工程、生产技术改造项目、电网小型基建、电力市场营销、电网数字化等其他工程在竣工投运后60日内完成工程结算编制和审核，财务部门在收到结算资料后120日内完成竣工决算报告编制。工程竣工决算整体时间原则上 控制在工程竣工投运后 6个月内完成。", "风险判定逻辑": "1.工程结算日期-投运日期>100天\n2.工程结算日期-投运日期>60天", "比对字段": ["工程结算日期", "投运日期"], "SQL": "```sql\nSELECT  *\nFROM    (\n            SELECT  proj.pspid AS PSPID    -- 项目编码\n                    ,proj.post1 AS POST1    -- 描述\n                    ,proj.prctr AS PRCTR    -- 利润中心\n                    ,proj.vbukr AS VBUKR    -- 公司代码\n                    ,proj.vernr AS VERNR    -- 负责人编码\n                    ,prps.posid AS POSID    -- 单体工程编码\n                    ,prps.post1 AS PRPS_POST1    -- 描述\n                    ,prps.stufe AS STUFE    -- 层级\n                    ,prps.prart AS PRART    -- 类型\n                    ,prps.usr08 AS USR08    -- 投运日期\n                    ,prps.objnr AS OBJNR    -- 对象号\n                    ,prps.pspnr AS PSPNR    -- WBS内码\n                    ,prps.zgcjsrq AS ZGCJSRQ    -- 工程结算日期\n                    ,prps.zgjsrq AS ZJGJSRQ    -- 竣工决算日期\n                    ,ROW_NUMBER() OVER(PARTITION BY proj.pspid, proj.post1, proj.prctr, proj.vbukr, proj.vernr, \n                                      prps.posid, prps.post1, prps.stufe, prps.prart, prps.usr08, \n                                      prps.objnr, prps.pspnr, prps.zgcjsrq, prps.zgjsrq \n                                      ORDER BY prps.usr08) row_index\n            FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj\n            LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS\n            ON      PROJ.PSPNR = prps.PSPHI  -- 外检关联(内码)\n            AND     LENGTH(TRIM(PRPS.PSPNR)) > 0\n            AND     PRPS.mandt = '880'\n            AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')\n            WHERE   proj.mandt = '880'\n            AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')\n            AND     proj.pspid in \n            ('18138721004F', '18138721004B', '18138721000U')  \n        ) \nWHERE   row_index = 1\n;\n```"}]}'

