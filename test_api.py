import json
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="",
)

def model_gen(prompt):
    result = client.chat.completions.create(
        model="deepseek/deepseek-r1-0528",
        # model="deepseek/deepseek-chat-v3-0324",
        messages=[
            {"role": "system", "content": "你是一个专业的审计专家，擅长分析各种审计项目并进行异常排查。"},
            {"role": "user", "content": prompt}
        ],
        stream=False,
        temperature=0.0
    )
    response = result.choices[0].message.content
    return response

# Part 1 得到异常排查方向
def get_error_directions(retrieved_cases , risk_points = None):
    SYS_MSG = '''我将提供几个审计案例，每个案例包括审计内容，风险与异常，和相应的政策和法规依据。
    同时，如果我给你了所有可能的审计风险点，则你可以参考这个总的审计风险点分类，来分析这些案例，但不能给出案例中不存在的排查方向。
    如果我没有给你所有可能的审计风险点，则请你直接分析。
    在最后统一地总结出这些审计案例中存在的异常标准，即哪里存在问题，接着针对总结出的异常问题，提出和这些审计案例类似的项目可以针对哪些方向进行异常排查，请你精简而准确地输出异常排查方向

    请按如下格式输出：
    审计内容：xxx
    相应适用的法律法规：xxx
    审计异常标准：
    xxx
    xxx
    异常排查方向：
    XXX
    XXX

    下面是提供的部分审计案例：'''

    suffix1 = "审计风险点：\n"

    suffix2 = "请根据上述的一些审计案例，分析总结，最终按规定格式输出。"

    if risk_points is None:
        prompt1 = SYS_MSG + retrieved_cases + suffix2
    else:
        prompt1 = SYS_MSG + retrieved_cases + suffix1 + risk_points + suffix2
    response = model_gen(prompt1)

    # print("Part 1 response: \n",response1)
    
    prompt2 = "请你抽取出下面这段文本最后总结出的异常排查方向，并直接将其输出：\n"
    extract_dir = model_gen(prompt2+response)
    print("Part 1 异常排查方向\n",extract_dir,"\n")
    return extract_dir

def get_overall_risk_points(kb_file):
    with open(kb_file, 'r', encoding='utf-8') as f:
        kb_cases = json.load(f)

    overall_audit_risk_points = '''审计风险点 审计风险描述\n'''
    for case in kb_cases:
        case_id = case.get("audit_case_id", "未知ID")
        risk_point = case.get("risk_point", "未知风险点")
        risk_point_description = case.get("risk_point_description", "无描述")
        overall_audit_risk_points += f"{case_id}. {risk_point} {risk_point_description}\n"
    
    return overall_audit_risk_points

# Part 2 确定审计风险点，并得到判定参数
def determine_get_checkitem(directions, kb_file):
    SYS_MSG2 = '''我将提供一个具体的审计项目经过分析之后，得到的可能存在的异常排查方向，以及所有的审计风险点和对应的审计风险描述。请你根据这个具体项目存在的这些异常排查方向，从全部的风险点中分析、筛选并最终选择出最匹配的一个或多个审计风险点，并输出相应的编号。若输出多个编号则每行输出一个。只需要输出数字编号，不要输出其他解释或无关内容。
    异常排查方向：
    '''
    overall_audit_risk_points = get_overall_risk_points(kb_file)

    prompt2 = SYS_MSG2 + directions + overall_audit_risk_points
    risk_points = model_gen(prompt2)
    print("Part 2 确定的审计风险点:\n", risk_points, "\n")

    def extract_risk_points_id(response):
        risk_points_id = []
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.isdigit():
                risk_points_id.append(line)
        return risk_points_id

    risk_points_id = extract_risk_points_id(risk_points)
    print("Part 2 选择的审计风险点编号：", risk_points_id)

    check_items = []
    with open(kb_file, 'r', encoding='utf-8') as f:
        kb_cases = json.load(f)
    for case in kb_cases:
        if case.get("audit_case_id") in risk_points_id:
            determination_parameter = case.get("determination_parameter", "无参数")
            print(f"Selected Risk Point: {case['audit_case_id']}\n判定参数：\n{determination_parameter}\n")
            check_items.append(case)
    return check_items

# Part 3 根据风险点和参数进行判定
def judge(check_items,retrieved_info):
    SYS_MSG4 = '''我将提供一个或多个审计风险点，以及风险点的描述和相应的判定参数，以及真实项目的多个日期（年月日），请你根据这些信息，判断真实项目在这些审计风险点上是否存在该风险，并对每个风险点输出判断结果。若真实项目的信息满足风险点对应的判定参数设置的规则，则判断结果为：“满足”，反之则判断结果为：“不满足”。请按照以下方式输出，不要输出其他解释或无关内容。
    审计风险点：xxx
    满足 / 不满足
    '''

    prompt4 = SYS_MSG4 
    for item in check_items:
        prompt4 += f"\n审计风险点：{item['risk_point']}\n"
        prompt4 += f"风险点描述：{item['risk_point_description']}\n"
        prompt4 += f"判定参数：{item['determination_parameter']}\n\n"

    prompt4 += retrieved_info
    response4 = model_gen(prompt4)
    print("Part 4 判断结果:\n", response4.strip(), "\n")
    return response4

def main():
# Part 0 召回项目的相关案例
    retrieved_cases = '''【案例一】审计内容: \n任期内，[某公司]45个项目预转资时间早于投产时间，涉及3829万元，如[某地区]110kV[变电站A]10kV[线路B]改造项目，预转资时间2020年8月31日，实际投产时间2020年11月23日；又如[某地区]110kV[变电站C]10kV[线路D]配套送出项目，预转资时间2021年12月31日，实际投产时间2022年6月26日。\n政策和法规: 政策依据：上述事项不符合《国家电网公司会计核算办法2021》（国网（财/2）469-2020）第七章第三节第二（五）点关于'（3）在建工程达到预定可使用状态，应当自达到预定可使用状态之日起，根据‘投运单’将工程成本全部暂估转资计入固定资产'的规定。引用法规：《国家电网公司会计核算办法2021》\n\n\n【案例二】\n审计内容: 资本性项目转资不规范。\n一是资产暂估转资不及时。检查2020年3月-2022年11月发生的18个技改项目及11个营销项目投资金额4636.68万元，发现其中4个技改项目、1个营销项目涉及金额1215.93万元转资滞后。如[某供电公司]10kV[变电站E]等32台高损配变改造项目，完工时间2022年9月，转资时间2022年12月，未在投产后30日内办理暂估预转资手续。\n二是资产转资缺少依据。[某供电公司]35kV[变电站F]主接线项目金额160万元，发生的竣工决算报告费用已支付，服务单位为[某会计师事务所]，在采购订单发票校验中未见相关发票。\n政策和法规: 政策依据：《国家电网有限公司工程财务管理办法》（国网（财/2）351-2022）第三十二条至第三十四条（内容略）。引用法规：《国家电网有限公司工程财务管理办法》《暂估工程成本明细表》\n\n【案例三】\n审计内容: 工程项目竣工转资不规范。\n工程项目转资不及时或提前转资。任期内203个项目转资时间晚于项目实际竣工日期，涉及结转资产8431.17万元，其中任期内竣工项目涉及78个，结转资产4800.42万元。抽查16个已完工项目，其中9个转资不及时，4个未经竣工验收提前结转资产。如：[某地区]110kV[变电站G]10kV[线路H]新建工程2019年10月竣工，2020年8月转资，超期235天；[某地区]110kV[变电站I]10kV[线路J]改造工程2020年8月竣工，2020年6月转资，提前49天转资。\n政策和法规: 政策依据：上述事项不符合《国家电网有限公司工程财务管理办法》（国家电网企管〔2019〕427号）第四十六条（内容略）。"'''

# Part 1 得到异常排查方向
    # kb_file = "/data2/ptj/proj/audit/kb_cases.json"
    # risk_points = get_overall_risk_points(kb_file)
    # dirs = get_error_directions(retrieved_cases,risk_points)
    dirs = get_error_directions(retrieved_cases)

# Part 2 确定审计风险点，并得到判定参数
    kb_file = "/data2/ptj/proj/audit/kb_cases.json"
    check_items = determine_get_checkitem(dirs,kb_file)
    
# Part 3 根据风险点和参数进行判定

    # retrieved_info = '''
    # 投运转资日期：20220506
    # 转资凭证日期：20211224
    # 投产日期：20211203
    # 资产价值日：20211120
    # '''
    retrieved_info = '''
    投运转资日期：2022年05月06日
    转资凭证日期：2021年12月24日
    投产日期：2021年12月03日
    资产价值日：2021年11月20日
    '''
    #价值偏离了，因为资产价值日 ≠ 投产当月
    #转资正常，转资凭证日期在投产日期之后30天内

    judgement = judge(check_items,retrieved_info)


if __name__ == "__main__":
    main()

# ICL_data = '''审计风险点	审计风险描述	判定参数
# 1. 项目验收资料缺失或不规范 验收资料缺失或未按规定格式提交，可能影响项目成果认定及后续资金结算  《项目验收报告》（非系统参数）、验收照片、验收签字记录等相关资料是否齐全
# 2. 合同执行情况与实际不符	实际执行金额或内容与合同约定不一致，存在超支、未执行或违规变更风险	合同原文、变更合同、付款记录、项目现场记录（系统/非系统参数）
# 3. 设备采购缺乏价格对比依据	设备采购未提供市场询价、比价或议价记录，存在采购价格偏高的风险	采购合同、采购清单、询价记录、同类设备市场价格信息（非系统参数）
# 4. 预算调整未备案或超审批权限	项目执行过程中预算调整未报备或超出原审批权限，影响资金使用合规性	《预算调整单》、预算审批流程记录（系统参数）、项目预算控制表
# 5. 关键节点延期未申报	关键进度节点延期未及时申报备案，影响整体项目进度和绩效评价	《进度计划表》与实际完成情况对比、延期说明材料、项目管理系统数据'''


#换成deepseek-r1
#排查方向给两个方案：
# 1.给定风险点，去确定排查方向，再根据排查方向去确定是哪些风险点
# 2.不给风险点，推理出排查方向

# 风险点总和

#使用ICL让模型归纳出可能的风险点，ICL自己用gpt造。有了风险点，生成对应的判定参数

#使用真样例生成假的样例，假样例（排查方向、风险点、判定参数）作为真实过程中的ICL

