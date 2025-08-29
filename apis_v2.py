from flask import Flask, request, jsonify, Response
import requests
import json
from Risk2SQL.infer_method import run_pipelines
from Summary import summary
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
            {"role": "user", "content": prompt}
        ],
        stream=False,
        temperature=0.0
    )
    response = result.choices[0].message.content
    return response

app = Flask(__name__)

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

def thinking_content(query):
    '''
    API 1
    输入：用户query
    输出：流程定位、项目范围、问题分类、问题分类+匹配的审计问题分类三四级（1:n）
    Process_orientation、Project_scope、Error_classification、Error_audit_q_classification_mapping
    '''
    Process_orientation, Project_scope, Error_classification, Error_audit_q_classification_mapping = [],"",[],[]
    #流程定位——待定

    #项目范围
    PROJECT_SCOPE_MSG = '''请你针对用户输入的提问（一个审计问题），输出这个审计项目的项目范围，包含：项目的组织、时间、一定是综合计划内的项目、是否是配网项目。注意输出时不要使用markdown格式。
    例如：
    用户输入：对2022-2024年南平公司光泽县配网项目转资异常分析
    输出：
    项目的组织是：南平公司光泽县
    项目的时间范围是：2022-2024年
    项目是综合计划内的项目
    项目是配网项目

下面是用户输入的提问：
'''
    Project_scope = model_gen(PROJECT_SCOPE_MSG + query)
    print("Project_scope: \n",Project_scope,"\n")

    #问题分类
    QUERY_TRANS_MSG = f'''请你将下列用户的query进行变换，把替换具体的项目时间、地点替换成“电网”。
    例如：
    用户query：对2022-2024年南平公司光泽县配网项目转资异常分析
    输出：电网配网项目转资异常分析
    
    用户query：{query}
    输出：'''
    query_trans = model_gen(QUERY_TRANS_MSG)
    print("query_trans: ",query_trans,"\n")

    original_response = model_gen(query_trans)
    print("original_response: \n",original_response,"\n")
    ERROR_CLS_EXTRACTION_MSG = f'''下面我给你的文本是模型对用户输入的一个审计问题的一个分析回复，请你抽取出模型回复中的“主要异常现象”部分，或者说“主要异常方面”部分，或者说“异常的主要类型及表现”部分（因为模型每次的回复都不一样，所以要抽取的部分可能会存在上述这些关键词，也可能不在上面说的这些里面，但是就是这类意思）。请注意只抽取出原文中的这一部分，只严格按照原文抽取，不要修改任何东西，直接输出抽取的内容，不输出其他无关的内容。
    例如：
    模型输出：
    # 电网配网项目转资异常分析

## 常见转资异常类型

1. **资产分类错误**
   - 资产类别与实物不符
   - 资产分类标准理解偏差
   - 混合资产未合理拆分

2. **价值计量问题**
   - 成本归集不完整
   - 费用分摊不合理
   - 资本化与费用化界限不清

3. **转资时点异常**
   - 提前或延迟转资
   - 投运时间与转资时间不匹配
   - 暂估转资后未及时调整

4.**资料不完整**
   - 缺少必要的验收文件
   - 结算资料不齐全
   - 资产清单不准确

## 异常原因分析

1. **管理流程因素**
   - 部门间协同不畅
   - 转资标准不统一
   - 缺乏有效监督机制

2. **系统因素**
   - 系统间数据不贯通
   - 系统功能不完善
   - 系统操作不规范

3. **人员因素**
   - 专业能力不足
   - 责任意识不强
   - 人员流动频繁

## 解决方案建议

1. **完善制度流程**
   - 制定明确的转资标准和操作规范
   - 建立跨部门协同机制
   - 实施转资质量考核

2. **加强系统支撑**
   - 实现业务财务系统集成
   - 开发转资辅助工具
   - 建立异常预警机制

3. **提升人员能力**
   - 开展专项培训
   - 建立专家支持团队
   - 实施岗位资格认证

4. **强化过程管控**
   - 建立转资前审核机制
   - 实施转资后评估
   - 定期开展专项检查

需要更详细分析或针对特定异常类型的解决方案，可进一步沟通。

    抽取内容：
1. **资产分类错误**
   - 资产类别与实物不符
   - 资产分类标准理解偏差
   - 混合资产未合理拆分

2. **价值计量问题**
   - 成本归集不完整
   - 费用分摊不合理
   - 资本化与费用化界限不清

3. **转资时点异常**
   - 提前或延迟转资
   - 投运时间与转资时间不匹配
   - 暂估转资后未及时调整

4.**资料不完整**
   - 缺少必要的验收文件
   - 结算资料不齐全
   - 资产清单不准确

    下面是模型的输出：
    {original_response}
    请你进行抽取，抽取内容：
    '''
    error_cls_extraction = model_gen(ERROR_CLS_EXTRACTION_MSG)
    print("error_cls_extraction: \n",error_cls_extraction,"\n")

    FINE_GRAINED_PROCESS_MSG = f'''请你对下面这段文本根据他内含的分点，进行切分，每一部分隔一行，并在每段开始先输出这段的小标题（原文抽取即可），再下一行输出这段的内容。注意你只能重复或抽取原文，不要输出其他的无关的东西
    例如：
    原文：
二、 主要异常现象
通过调阅财务系统、基建管理系统及项目档案，发现转资异常主要集中在以下几个方面：
转资时效性异常（延迟转资）：
现象： 大量项目已达到“预定可使用状态”（即已投产送电），但长期挂列“在建工程”科目，未能及时办理转资手续。延迟时间短则数月，长则超过一年，导致固定资产折旧计提滞后，影响当期损益的准确性。
资产价值准确性异常（账实不符）：
现象： 转资资产价值与项目实际形成资产价值存在偏差。
价值虚高： 转资金额包含了不应资本化的费用（如项目前期经费、违规费用等）。
价值偏低： 未能将全部应资本化的支出纳入转资范围，如部分材料、安装费用等被遗漏，导致部分资产“游离”在账外。
拆分不准： 资产卡片数量、型号、地理位置（线路杆号、配变台区号）与现场实物无法一一对应，给后续资产巡检、运维带来困难。
流程规范性异常（资料缺失与卡滞）：
现象： 转资所需的支撑性文件不齐全、不规范，导致流程在财务、物资、运维等部门间反复退回和补充。
竣工决算报告滞后或质量差： 报告内容不完整，数据勾稽关系错误。
物资清理不到位： 项目余料未办理退库或假退库手续，剩余物资成本仍挂在项目账上。
验收手续不完善： 缺少正式的竣工验收签证书，或签字流程不完整。

输出：
转资时效性异常（延迟转资）
转资时效性异常（延迟转资）：
现象： 大量项目已达到“预定可使用状态”（即已投产送电），但长期挂列“在建工程”科目，未能及时办理转资手续。延迟时间短则数月，长则超过一年，导致固定资产折旧计提滞后，影响当期损益的准确性。

资产价值准确性异常（账实不符）
资产价值准确性异常（账实不符）：
现象： 转资资产价值与项目实际形成资产价值存在偏差。
价值虚高： 转资金额包含了不应资本化的费用（如项目前期经费、违规费用等）。
价值偏低： 未能将全部应资本化的支出纳入转资范围，如部分材料、安装费用等被遗漏，导致部分资产“游离”在账外。
拆分不准： 资产卡片数量、型号、地理位置（线路杆号、配变台区号）与现场实物无法一一对应，给后续资产巡检、运维带来困难。

流程规范性异常（资料缺失与卡滞）
流程规范性异常（资料缺失与卡滞）：
现象： 转资所需的支撑性文件不齐全、不规范，导致流程在财务、物资、运维等部门间反复退回和补充。
竣工决算报告滞后或质量差： 报告内容不完整，数据勾稽关系错误。
物资清理不到位： 项目余料未办理退库或假退库手续，剩余物资成本仍挂在项目账上。
验收手续不完善： 缺少正式的竣工验收签证书，或签字流程不完整。

原文：{error_cls_extraction}
输出：'''

    error_fine_grained_process = model_gen(FINE_GRAINED_PROCESS_MSG)
    print("error_fine_grained_process: \n",error_fine_grained_process,"\n") 

    error_parts_all = [p.strip() for p in error_fine_grained_process.split("\n\n") if p.strip()]
    error_title = [p.splitlines()[0] for p in error_parts_all]
    error_part = ["\n".join(p.splitlines()[1:]) for p in error_parts_all]

    Error_classification = error_part

    #问题分类+匹配的审计问题分类三四级（1:n）
    #读取excel文件
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "data", "业数审汇总+案例数据20250822.xlsm")
    data = load_excel_data(file_path)

    for i,item in enumerate(error_part):
        for j in range(7):
            audit_q_cls_level3 = get_value_by_column_row(data, "审计问题分类-三级", j) or ""
            audit_q_cls_level4 = get_value_by_column_row(data, "审计问题分类-四级", j) or ""
            MATCH_MSG = '''请你判断，下面给定的一个审计问题异常分类，和给定的文本是否是相关的，是则输出“是”，否则输出“否”。只要关键词有相关，即可输出“是”，实在是没有关联的，才输出“否”。不要输出其他无关内容，只输出“是”/“否”。
            例如：
            异常分类：
            1. **资产分类错误**\n   - 设备类型与资产卡片不符\n   - 资产分类标准执行偏差
            文本：建账建卡不规范\n资产分类异常
            输出：是
            
            异常分类：
            3. **价值异常**\n   - 单位造价偏离合理范围\n   - 总价与分项合计不符\n   - 费用分摊不合理
            文本：项目暂估转资及决算不规范\n资产价值与实际造价偏差大
            输出：是
            
            异常分类：
            4. **时间节点问题**\n   - 转资时间滞后于实际投运时间\n   - 转资周期过长', '5. **资料不完整**\n   - 缺少验收报告\n   - 缺少资产清单\n   - 缺少合同结算资料
            文本：项目暂估转资及决算不规范\n决算转资不及时
            输出：是
            
            异常分类：{}
            文本：{}
            输出：'''
            # judgement_l3 = model_gen(MATCH_MSG.format(item,audit_q_cls_level3)).strip()
            # judgement_l4 = model_gen(MATCH_MSG.format(item,audit_q_cls_level4)).strip()
            long_str = str(audit_q_cls_level3)+"，"+str(audit_q_cls_level4)
            judgement = model_gen(MATCH_MSG.format(item,long_str)).strip()
            if judgement == "是":
                Error_audit_q_classification_mapping.append({"content":error_title[i]+"——"+long_str,"index":j})
            

    print("Process_orientation: ",Process_orientation)
    print("Project_scope: ",Project_scope)
    print("Error_classification: ",Error_classification)
    print("Error_audit_q_classification_mapping: ",Error_audit_q_classification_mapping)
    return Process_orientation,Project_scope,Error_classification,Error_audit_q_classification_mapping

def thinking_graph(Error_audit_q_classification_mapping):
    '''
    API 2
    输入：时间异常——审计问题分类三，四级
    输出：
1、问题分类
2、风险点
3、问题依据
4、判定逻辑
5、业务活动
6、业务对象【图谱形式给出、上下级关系前端去渲染展示】
    Error_cls、Risk_point、Grounds、Logic、Service_activity、Service_object
    '''
    result_json = {"entities":[],"relationships":[]}
    #读取excel文件
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "data", "业数审汇总+案例数据20250822.xlsm")
    data = load_excel_data(file_path)

    seen_Error_cls = set()
    seen_Risk_point = set()
    for item in Error_audit_q_classification_mapping:
        index = item["index"]
        content = item["content"]
        Error_cls = content.split("——")[0]
        if Error_cls not in seen_Error_cls:
            result_json["entities"].append({"name":Error_cls,"type":"Error_cls"})
            seen_Error_cls.add(Error_cls)
        
        risk_point = get_value_by_column_row(data, "审计风险点", index)
        if risk_point not in seen_Risk_point:
            result_json["entities"].append({"name":risk_point,"type":"Risk_point"})
            seen_Risk_point.add(risk_point)
        
        result_json["relationships"].append({"from_entity":Error_cls,"to_entity":risk_point,"relationship":"belongs_to"})

        grounds = get_value_by_column_row(data, "政策制度及管理办法", index)
        result_json["entities"].append({"name":grounds,"type":"Grounds"})
        result_json["relationships"].append({"from_entity":risk_point,"to_entity":grounds,"relationship":"belongs_to"})

        logic = get_value_by_column_row(data, "风险判定逻辑", index)
        result_json["entities"].append({"name":logic,"type":"Logic"})
        result_json["relationships"].append({"from_entity":risk_point,"to_entity":logic,"relationship":"belongs_to"})

        service_act = get_value_by_column_row(data, "业财流程及活动", index)
        result_json["entities"].append({"name":service_act,"type":"Service_activity"})
        result_json["relationships"].append({"from_entity":risk_point,"to_entity":service_act,"relationship":"belongs_to"})
        
        service_obj = get_value_by_column_row(data, "业务对象", index)
        result_json["entities"].append({"name":service_obj,"type":"Service_object"})
        result_json["relationships"].append({"from_entity":risk_point,"to_entity":service_obj,"relationship":"belongs_to"})
    
    print(result_json)
    return result_json

# API 1
@app.route('/api/thinking_content', methods=['POST'])
def process_tc():
    data = request.get_json()
    query = data.get("query", "")
    Process_orientation,Project_scope,Error_classification,Error_audit_q_classification_mapping= thinking_content(query)
    return app.response_class(
        response=json.dumps({"Process_orientation": Process_orientation,
                             "Project_scope":Project_scope,
                             "Error_classification":Error_classification,
                             "Error_audit_q_classification_mapping":Error_audit_q_classification_mapping}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# API 2
@app.route('/api/thinking_graph', methods=['POST'])
def process_tg():
    data = request.get_json()
    Error_audit_q_classification_mapping = data.get("Error_audit_q_classification_mapping", "")
    result_json = thinking_graph(Error_audit_q_classification_mapping)
    return app.response_class(
        response=json.dumps({"result_json": result_json}, ensure_ascii=False),
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
        response=json.dumps({"result": {"output": output, "think_graph": graph}}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# API 4
@app.route('/api/task_plan', methods=['POST'])
def process_tp():
    data = request.get_json()
    project_scope = data.get("project_scope", "")
    risk2method = data.get("risk2method", "")
    result = summary.summary_Method(project_scope, risk2method)
    return app.response_class(
        response=json.dumps({"result": result}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

    #API1
    # thinking_content("对2022-2024年南平公司光泽县配网项目转资异常分析")

    #API2
    # para = [{'content': '资产价值异常——建账建卡不规范，资产分类异常', 'index': 0}, {'content': '资产价值异常——项目暂估转资及决算不规范，nan', 'index': 4}, {'content': '时间节点异常——项目暂估转资及决算不规范，1.工程未竣工提前暂估资产\n2.暂估转资不及时', 'index': 1}, {'content': '时间节点异常——项目暂估转资及决算不规范，决算转资不及时', 'index': 3}]
    # thinking_graph(para)

