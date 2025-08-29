'''
    API Part4 总结
    输入：
        前三个API输出的项目范围、
    输出：
        完整的排查步骤

'''

import json


# API1 输出
PROJECT_RANGE = ""
# API2 输出
RISKS = []
# API3 输出
RISK2METHOD = [
    {
        "风险点": "预转资异常",
        "风险判定逻辑": "1.预转资日期＞投运日期\n2.预转资日期-投运日期＞30天",
        "比对字段": [
            "预转资日期",
            "投运日期"
        ],
        "审计风险描述": "对比项目投运日期和预转资日期，当预转资日期 >投运日期 + 30天，视为预转资超期，当预转资日期 <投运日期，视为预转资提前。"
    },
    {
        "风险点": "审定结算不及时",
        "风险判定逻辑": "1.工程结算日期-投运日期>100天\n2.工程结算日期-投运日期>60天",
        "比对字段": [
            "工程结算日期",
            "投运日期"
        ],
        "审计风险描述": "对比项目投运日期和工程结算日期:\n1.项目类型为11、13、15，工程结算日期>投运日期+100天\n2.其他资本性项目，工程结算日期>投运日期+60天"
    }
    ]

def summary_Method(PROCESS_TYPE, PROBLEM_TYPE, PROJECT_SCOPE, PROBLEM_MAPPING,
                   RISKS, RISK_GROUNDS, LOGIC, PROCESS_ITEM, SERVICE_OBJECT,
                   RISK2METHOD, SQL):

    OUTPUT = ""

    if PROCESS_TYPE:
        OUTPUT += "流程定位："
        if type(PROCESS_TYPE) is list:
            for process in PROCESS_TYPE:
                OUTPUT += f"{process}; "
            OUTPUT += "\n"
        elif type(PROCESS_TYPE) is str:
            OUTPUT += f"{PROCESS_TYPE}\n"

    if PROBLEM_TYPE:
        OUTPUT += "问题分类："
        if type(PROBLEM_TYPE) is list:
            for type_ in PROBLEM_TYPE:
                OUTPUT += f"{type_}; "
            OUTPUT += "\n"
        elif type(PROBLEM_TYPE) is str:
            OUTPUT += f"{PROBLEM_TYPE}\n"

    if PROJECT_SCOPE:
        OUTPUT += f"项目范围："
        if type(PROJECT_SCOPE) is list:
            for project_scope in PROJECT_SCOPE:
                OUTPUT += f"{project_scope}; "
            OUTPUT += "\n"
        elif type(PROJECT_SCOPE) is str:
            OUTPUT += f"{PROJECT_SCOPE}\n"

    if PROBLEM_MAPPING:
        OUTPUT += "问题分类映射到审计问题："
        if type(PROBLEM_MAPPING) is list:
            for mapping_ in PROBLEM_MAPPING:
                OUTPUT += f"{mapping_}; "
            OUTPUT += "\n"
        elif type(PROBLEM_MAPPING) is str:
            OUTPUT += f"{PROBLEM_MAPPING}\n"

    if RISKS:
        OUTPUT += "风险点："
        if type(RISKS) is list:
            for risk in RISKS:
                OUTPUT += f"{risk}; "
            OUTPUT += "\n"
        elif type(RISKS) is str:
            OUTPUT += f"{RISKS}\n"

    if RISK_GROUNDS:
        OUTPUT += "问题依据："
        if type(RISK_GROUNDS) is list:
            for risk_ground in RISK_GROUNDS:
                OUTPUT += f"{risk_ground}; "
            OUTPUT += "\n"
        elif type(RISK_GROUNDS) is str:
            OUTPUT += f"{RISK_GROUNDS}\n"

    if LOGIC:
        OUTPUT += "判定逻辑："
        if type(LOGIC) is list:
            for logic in LOGIC:
                OUTPUT += f"{logic}; "
            OUTPUT += "\n"
        elif type(LOGIC) is str:
            OUTPUT += f"{LOGIC}\n"

    if PROCESS_ITEM:
        OUTPUT += f"业务活动："
        if type(PROCESS_ITEM) is list:
            for process_item in PROCESS_ITEM:
                OUTPUT += f"{process_item}; "
            OUTPUT += "\n"
        elif type(PROCESS_ITEM) is str:
            OUTPUT += f"{PROCESS_ITEM}\n"

    if SERVICE_OBJECT:
        OUTPUT += f"业务对象："
        if type(SERVICE_OBJECT) is list:
            for service_object in SERVICE_OBJECT:
                OUTPUT += f"{service_object}; "
            OUTPUT += "\n"
        elif type(SERVICE_OBJECT) is str:
            OUTPUT += f"{SERVICE_OBJECT}\n"


    if RISK2METHOD:
        OUTPUT += f"风险点目标字段："
        if type(RISK2METHOD) is list:
            for risk2method in RISK2METHOD:
                OUTPUT += f"{risk2method}; "
            OUTPUT += "\n"
        elif type(RISK2METHOD) is str:
            OUTPUT += f"{RISK2METHOD}; \n"

    if SQL:
        OUTPUT += f"SQL文件："
        if type(SQL) is list:
            for sql in SQL:
                OUTPUT += f"{sql}; "
            OUTPUT += "\n"
        elif type(SQL) is str:
            OUTPUT += f"{SQL}; \n"

    # for cnt, RISK in enumerate(RISK2METHOD):
    #
    #     risk = RISK["风险点"]
    #     key_data = "、".join(RISK["比对字段"])
    #     desc = RISK["审计风险描述"].replace("\n", " ")
    #     policy = RISK["政策制度及管理办法"]
    #     logic = RISK["风险判定逻辑"]
    #
    #     OUTPUT += (
    #         f"\n({cnt + 2}){risk}排查：这一风险点指{desc}，我将利用业数图谱推理出“{key_data}”关键数据的来源，通过SQL脚本+API从数据中台相关数据；")
    #     #                    f"根据{policy}，这一风险点的判断逻辑是{logic}")

    return OUTPUT

#     OUTPUT = '''
# (1)项目清单范围确定：通过SQL脚本+API从数据中台获取2022至2024年度综合计划项目，筛选出南平公司光泽县公司负责的已竣工资本性投资项目清单。'''
#     # (2)预转资异常排查：利用业数图谱推理出“工程投运日期、第一次转资日期”关键数据的来源，通过SQL脚本+API从数据中台相关数据，结合审计依据，根据逻辑推理的工程预转资异常判断规则，排查确定预转资提前或超期疑点。
#     # (3)工程正式转资异常排查
#     # (4)资产账面价值与实际造价不符排查
#     # (5).....
#     for cnt, RISK in enumerate(RISK2METHOD):
#         risk = RISK["风险点"]
#         key_data = "、".join(RISK["比对字段"])
#         desc = RISK["审计风险描述"].replace("\n", " ")
#         policy = RISK["政策制度及管理办法"]
#         logic = RISK["风险判定逻辑"]
#
#         OUTPUT += (f"\n({cnt+2}){risk}排查：这一风险点指{desc}，我将利用业数图谱推理出“{key_data}”关键数据的来源，通过SQL脚本+API从数据中台相关数据；"
#                    f"根据{policy}，这一风险点的判断逻辑是{logic}")


    # RISKS = INPUT.get("risks")
    # RISK_RANGE=
    # PROJECT_RANGE=""



if __name__ == '__main__':
    output = summary_Method(PROJECT_RANGE, RISKS, RISK2METHOD)
    print(output)