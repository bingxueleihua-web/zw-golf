import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ================= 1. 基础配置 =================
# 数据存储文件名（自动保存在云端服务器或本地文件夹）
DATA_FILE = "zw_golf_finance_v3.csv"

# 设置页面标题和图标（手机端访问时会显示在标题栏）
st.set_page_config(
    page_title="中闻高尔夫财务", 
    page_icon="⛳", 
    layout="wide"
)

# 自定义 CSS 让界面在手机上更美观
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据处理函数 =================
def init_data():
    """初始化数据库文件，定义所有你要求的字段"""
    if not os.path.exists(DATA_FILE):
        cols = ["日期", "主分类", "科目", "金额", "球场地点", "参与人数", "经手人", "备注(欠费记录)"]
        df = pd.DataFrame(columns=cols)
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_data():
    return pd.read_csv(DATA_FILE, encoding='utf-8-sig')

def save_data(date, main_type, sub_cat, amount, loc, people, handler, note):
    # 财务逻辑：支出自动存为负数，方便汇总计算
    final_amount = amount if main_type == "收入" else -amount
    new_row = {
        "日期": date,
        "主分类": main_type,
        "科目": sub_cat,
        "金额": final_amount,
        "球场地点": loc,
        "参与人数": people,
        "经手人": handler,
        "备注(欠费记录)": note
    }
    df = pd.DataFrame([new_row])
    df.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')

# 执行初始化
init_data()

# ================= 3. 侧边栏：录入界面 =================
st.sidebar.header("📝 财务数据录入")
with st.sidebar.form("entry_form", clear_on_submit=True):
    in_out = st.radio("交易属性", ["收入", "支出"], horizontal=True)
    
    # 联动菜单：根据收/支显示不同的科目
    if in_out == "收入":
        category = st.selectbox("科目", ["会费", "报名费", "赞助费", "打球费", "其他"])
    else:
        category = st.selectbox("科目", ["餐饮费", "奖品费", "物料费(球帽/球衣)", "打球费", "其他"])
        
    date_val = st.date_input("日期", datetime.now())
    amount_val = st.number_input("金额 (元)", min_value=0.0, step=10.0)
    loc_val = st.text_input("打球地点", placeholder="如：北京天安假日")
    people_val = st.number_input("参与人数", min_value=0, step=1)
    handler_val = st.text_input("经手人", value="球队财务")
    note_val = st.text_area("备注 (如：谁未缴费)")
    
    submitted = st.form_submit_button("确认保存", use_container_width=True)
    if submitted:
        save_data(date_val, in_out, category, amount_val, loc_val, people_val, handler_val, note_val)
        st.sidebar.success("✅ 记录成功！")

# ================= 4. 主界面：报表分析 =================
st.title("⛳ 中闻律师高尔夫球队财务管理")

data = load_data()
data['日期'] = pd.to_datetime(data['日期'])

# --- 顶部：核心指标卡 ---
in_total = data[data["金额"] > 0]["金额"].sum()
out_total = abs(data[data["金额"] < 0]["金额"].sum())
balance = in_total - out_total

col1, col2, col3 = st.columns(3)
col1.metric("累计总收入", f"¥{in_total:,.2f}")
col2.metric("累计总支出", f"¥{out_total:,.2f}")
col3.metric("当前总结余", f"¥{balance:,.2f}")

st.divider()

# --- 中部：分类统计 ---
tab1, tab2 = st.tabs(["📊 收支明细表", "⚠️ 欠费/待跟进"])

with tab1:
    # 年度/月度筛选（可选）
    st.subheader("全量流水记录")
    # 按日期倒序排列，最新的在最上面
    st.dataframe(data.sort_values("日期", ascending=False), use_container_width=True)
    
    # 导出功能
    csv = data.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 导出 Excel 兼容格式 (CSV)", data=csv, file_name="中闻高尔夫财务报表.csv")

with tab2:
    st.subheader("异常/欠费跟进单")
    # 自动识别备注里含有“未交”、“欠”等字眼的行
    unpaid = data[data["备注(欠费记录)"].str.contains("未交|未缴|欠|未付", na=False)]
    if not unpaid.empty:
        st.warning("以下记录存在未完成的财务项：")
        st.table(unpaid[["日期", "科目", "金额", "备注(欠费记录)"]])
    else:
        st.success("🎉 目前所有款项均已对齐。")
