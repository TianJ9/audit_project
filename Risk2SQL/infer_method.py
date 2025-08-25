'''
    API Part3 问数
    输入：
        审计风险点；业数图谱
    输出：
        每个风险点的判断逻辑（比较哪些数据）
        取数的SQL脚本

'''

import json
import re
import openpyxl
from openai import OpenAI
from openpyxl import load_workbook
import os
from jinja2 import Template

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="",
)

model = "deepseek-reasoner"
# model="deepseek-chat"


# 可以按需改写为本地部署的生成方式
def model_gen(prompt):
    result = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个专业的审计专家，擅长分析各种审计项目并进行异常排查。"},
            {"role": "user", "content": prompt}
        ],
        stream=False,
        temperature=0.0
    )
    response = result.choices[0].message.content
    # print(response)
    return response


def clean_model_json(text: str):
    trans_map = str.maketrans({
        '（': '(',
        '）': ')',
        '，': ',',
        '：': ':',
        '“': '"',
        '”': '"',
        '’': "'",
        '‘': "'"
    })
    cleaned = text.translate(trans_map)

    match = re.search(r'\[.*\]', cleaned, flags=re.S)
    if match:
        cleaned = match.group(0)

    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    try:
        return cleaned
    except json.JSONDecodeError as e:
        print("JSON 解析失败:", e)
        print("清洗后的文本:", cleaned)
        return None


file_path = "KnowledgeGraph.xlsx"
output_path = f"fields_from_{model}.json"



print("API 3: 根据风险点找到需要比对的字段，同时生成取数SQL脚本")
print(f"使用{model}模型演示中")


# Step1 遍历1.1中的数据表，并
def find_risk_rows(file_path, search_value):
    print("取数Step1: 获取风险点对应描述、判定逻辑和判定参数")
    # 1. 读入文件
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    # 2. 查找第二行中的目标列索引
    target_headers = ["审计风险点", "审计风险描述", "政策制度及管理办法", "风险判定逻辑", "判定参数"]
                      # "中台共享层表单编码"]
    col_indices = {}

    for col in range(1, ws.max_column + 1):
        cell_value = ws.cell(row=2, column=col).value
        if cell_value in target_headers:
            col_indices[cell_value] = col

    print("找到的列索引：", col_indices)

    # 检查是否找齐
    if len(col_indices) < len(target_headers):
        print("警告：部分目标列没有找到！")

    # 3. 遍历对应列，查找匹配行
    matched_rows = []
    for header, col in col_indices.items():
        for row in range(3, ws.max_row + 1):  # 从第3行开始，因为第2行是表头
            cell_value = ws.cell(row=row, column=col).value
            if cell_value == search_value:
                matched_rows.append(row)

    matched_data = []
    # 4. 输出结果
    for row in matched_rows:
        row_data = {header: ws.cell(row=row, column=col_indices[header]).value for header in col_indices}
        print(f"匹配行 {row} 的数据: {row_data}")
        matched_data.append(row_data)
    return matched_rows, matched_data


# Step2 针对每个风险点，输出判别逻辑：针对每个风险点，拿什么字段和什么字段对比
def choose_process(LOGIC):
    print("取数Step2: 根据风险点描述与逻辑，找出需要比对的字段")
    PROMPT_TEMPLATE = '''
    你的任务是：根据给定的判定逻辑，给定需要判别的字段，如
    
    - 示例判别逻辑：“资产转资金额/采购订单的设备购置价格>3倍”
    - 示例输出：["资产转资金额", "采购订单的设备购置价格"]
    
    输出要求：
    - 使用列表输出，每个元素为一个用于判别比较的字段
    - 严格基于判别逻辑，不要编造
    
    输入：
    - 判别逻辑："{logic}"
    '''

    prompt = PROMPT_TEMPLATE.format(logic=LOGIC)
    while True:
        # response = model_gen(prompt).replace("'''", "").replace("json", "").strip()
        response = clean_model_json(model_gen(prompt))
        try:
            chosen_fields = json.loads(response)
            break
        except Exception:
            print("Unformatted response, try again")
    print(f"chosen fields: {chosen_fields}\n")
    return chosen_fields


# Step3 完成表格对应数据的映射，获取用于生成SQL的字段
def find_fields_by_table(table_name, target_fields):
    print("取数Step3: 根据源数据进行映射，找到生成SQL所需参数")
    """
    file_path: Excel文件路径
    table_name: 要匹配的表名（第8列）
    target_fields: 目标字段列表，用于匹配第9列
    """
    file_path = "data/SourceData.xlsx"
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    matched_rows = []

    # 1. 遍历第8列，找到表名匹配的行
    for row in range(1, ws.max_row + 1):
        cell_value = ws.cell(row=row, column=8).value
        if cell_value == table_name:
            matched_rows.append(row)

    print(f"匹配表名 '{table_name}' 的行号: {matched_rows}")

    # 2. 遍历第9列，查找目标字段
    results = []
    for row in matched_rows:
        cell_value = ws.cell(row=row, column=9).value
        if cell_value is None:
            continue
        for field in target_fields:
            if field in str(cell_value):  # 包含匹配
                results.append({
                    "目标字段": field,
                    "整单元格内容": cell_value
                })

    # 3. 输出结果
    filtered = []
    for r in results:
        if r not in filtered:
            filtered.append(r)

    print(filtered)
    return filtered



# Step4 生成SQL
def generate_SQL(risk, target_fields, key_fields):
    print("取数Step4: 生成SQL文件")
    PROMPT_TEMPLATE = '''
    根据关键字段和目标字段，仿照下面的SQL脚本的格式，写一个取数脚本，只返回脚本
    
    关键字段：
    {key_fields}
    目标字段：
    {target_fields}
    脚本：
    SELECT  *
    FROM    (
                SELECT  proj.pspid AS prj_code    -- 项目编码
                        ,proj.post1 AS prj_name    -- 项目名称
                        ,prps.stufe AS prj_level    -- 层级
                        ,substr(prps.posid, 1, 14) single_prj_code_14    -- 前14位
                        ,prps.posid AS single_prj_code    -- 单体工程编码
                        ,prps.post1 AS single_prj_name    -- 单体工程名称
                        ,prps.usr08 AS operation_start_date    -- 转资凭证日期（竣工验收日期）
                        ,bkpf.bldat AS capitial_date    -- 投运转资日期
                        ,ROW_NUMBER() OVER(PARTITION BY proj.pspid ,proj.post1 ,prps.stufe ,substr(prps.posid, 1, 14) ,prps.posid ,prps.post1 ,prps.usr08 ORDER BY bkpf.bldat) row_index
                FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
                LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
                ON      PROJ.PSPNR = prps.PSPHI  -- 外检关联(内码)
                AND     LENGTH(TRIM(PRPS.PSPNR)) > 0
                AND     prps.stufe IN (1, 2)
                AND     PRPS.mandt = '880'
                AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps') LEFT
                JOIN    (    --过滤条件
                            SELECT  prj_code
                                    ,COUNT(DISTINCT single_prj_code_14) AS NUM    -- 差异数
                            FROM    (
                                        SELECT  DISTINCT proj.pspid AS prj_code    -- 项目编码
                                                ,substr(prps.posid, 1, 14) single_prj_code_14    -- 前14位
                                        FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
                                        LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
                                        ON      PROJ.PSPNR = prps.PSPHI
                                        AND     LENGTH(TRIM(PRPS.PSPNR)) > 0
                                        AND     prps.stufe IN (1, 2)
                                        AND     PRPS.mandt = '880'
                                        AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')
                                        WHERE   proj.mandt = '880'
                                        AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')
                                    ) 
                            GROUP BY prj_code
                        ) mid_tmp_filter_table
                ON      mid_tmp_filter_table.prj_code = proj.pspid
                LEFT JOIN (
                              SELECT  gjahr    -- 会计年度
                                      ,belnr    -- 会计凭证编码
                                      ,bukrs    -- 公司代码
                                      ,mandt    -- 客户端
                                      ,sgtxt    -- 外键
                                      ,hkont
                              FROM    pro_dwh_erp_prd.ods_erp_zltp_erp_bseg
                          ) bseg
                ON      substr(bseg.sgtxt, 5, 14) = substr(prps.posid, 1, 14)    -- 外键
                AND     bseg.mandt = '880'
                AND     substr(bseg.hkont, 1, 4) = '1601' 
                LEFT JOIN    pro_dwh_erp_prd.ods_erp_p00_sapsr3_bkpf bkpf
                ON      bseg.bukrs = bkpf.bukrs    -- 外键盘
                AND     bseg.belnr = bkpf.belnr
                AND     bseg.gjahr = bkpf.gjahr
                AND     bkpf.ds = max_pt('pro_dwh_erp_prd.ods_erp_p00_sapsr3_bkpf')
                WHERE   proj.mandt = '880'
                AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')
                AND     CASE WHEN mid_tmp_filter_table.NUM == 1 THEN prps.stufe = 1 ELSE prps.stufe = 2 END
                AND     proj.pspid in 
                ('18138721004F', '18138721004B', '18138721000U')  
                -- '18138119006D'  
            ) 
    WHERE   row_index = 1
    ;
    '''

    prompt = PROMPT_TEMPLATE.format(key_fields=key_fields, target_fields=target_fields)
    while True:
        try:
            response = model_gen(prompt)
            break
        except Exception as e:
            print(e)
    # output_name = "_".join(target_fields)
    output_path = f"{risk}_{model}_{target_fields}.sql"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)


def pipeline(risk):
    print(f"正在为风险点{risk}进行查数操作")
    file_path = "data/KG.xlsm"  # 你的xlsx路径
    rows, rows_data = find_risk_rows(file_path, risk)
    output = []
    for cnt, item in enumerate(rows_data):
        logic = item["风险判定逻辑"]
        chosen_fields = choose_process(logic)

        epoch = {
            "风险点": risk,
            "审计风险描述": item["审计风险描述"],
            "政策制度及管理办法": item["政策制度及管理办法"],
            "风险判定逻辑": logic,
            "比对字段": chosen_fields,

        }
        output.append(epoch)

        if "." in item["中台共享层表单编码"] and len(item["中台共享层表单编码"].splitlines()) > 1:
            table_names = [line.split('.', 1)[1] for line in item["中台共享层表单编码"].splitlines()]
        else:
            table_names = [item["中台共享层表单编码"]]

        for table_name in table_names:
            target_fields_for_sql = find_fields_by_table(table_name, chosen_fields)

            for instance in target_fields_for_sql:
                target_fields = instance["目标字段"]
                key_fields = instance["整单元格内容"]
                generate_SQL(risk, target_fields, key_fields)

    return output

def main():
    # 输入风险点
    risks = [
        "预转资异常",
        "审定结算不及时"
    ]
    output = []
    for risk in risks:
        output.extend(pipeline(risk))
    with open(f"{model}.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()

