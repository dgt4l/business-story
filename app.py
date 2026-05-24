import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Business Story")

@st.cache_data
def load_data():
    return pd.read_csv("business_data.csv", parse_dates=["date"])

def render_overview(df):
    st.title("Шаг 1: Общая динамика бизнеса")
    st.markdown("Анализ ключевых финансовых показателей за исследуемый период демонстрирует стабильный рост операционных метрик.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Общая выручка", f"${df['revenue'].sum():,.0f}")
    col2.metric("Общая прибыль", f"${df['profit'].sum():,.0f}")
    col3.metric("Средняя удовлетворенность", f"{df['customer_satisfaction'].mean():.2f}")

    monthly = df.groupby(pd.Grouper(key='date', freq='ME'))[['revenue', 'profit']].sum().reset_index()
    fig = px.line(monthly, x='date', y=['revenue', 'profit'], title='Динамика выручки и прибыли')
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

def render_anomaly(df):
    st.title("Шаг 2: Выявление проблемных зон лояльности")
    st.markdown("При анализе метрики `customer_satisfaction` в разрезе клиентских сегментов выявляется систематическое отставание сегмента **Budget**.")
    
    seg_sat = df.groupby('segment')['customer_satisfaction'].mean().reset_index().sort_values('customer_satisfaction')
    fig = px.bar(seg_sat, x='segment', y='customer_satisfaction', color='segment', title='Средняя удовлетворенность по сегментам')
    
    if 'Budget' in df['segment'].values:
        budget_sat = seg_sat[seg_sat['segment'] == 'Budget']['customer_satisfaction'].values[0]
        fig.add_annotation(x='Budget', y=budget_sat, text="Низкий показатель", showarrow=True, arrowhead=1, ay=-40)
        
    st.plotly_chart(fig, use_container_width=True)

def render_segments(df):
    st.title("Шаг 3: Оценка финансового вклада сегментов")
    st.markdown("Гипотеза: компенсирует ли сегмент Budget низкую лояльность высокими объемами продаж? Распределение на графике опровергает это: Budget генерирует наименьший объем прибыли и выручки среди всех групп.")
    
    seg_data = df.groupby('segment').agg({'revenue': 'sum', 'profit': 'sum', 'units_sold': 'sum'}).reset_index()
    fig = px.scatter(seg_data, x='revenue', y='profit', size='units_sold', color='segment',
                     hover_data=['units_sold'], title='Выручка и прибыль (размер пузырька - объем продаж)', size_max=50)
    st.plotly_chart(fig, use_container_width=True)

def render_cause(df):
    st.title("Шаг 4: Локализация отклонений")
    st.markdown("Детализация метрики удовлетворенности показывает, что пересечение сегмента Budget с категорией **Electronics** образует наиболее проблемную зону (значение падает ниже 3.0).")
    
    pivot = df.pivot_table(values='customer_satisfaction', index='category', columns='segment', aggfunc='mean')
    fig = px.imshow(pivot, text_auto=".2f", title='Матрица удовлетворенности: Категория / Сегмент', aspect='auto', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

def render_solution(df):
    st.title("Шаг 5: Моделирование стратегии")
    st.markdown("Оценка экономического эффекта от конвертации части клиентов сегмента Budget в сегмент Standard. *(Расчет основан на разнице прибыльности сегментов: конвертация увеличивает доходность в ~1.66 раза)*.")
    
    conversion_rate = st.slider("Доля конвертации Budget -> Standard (%)", 0, 100, 20)
    
    df_sim = df.copy()
    mask_budget = df_sim['segment'] == 'Budget'
    
    original_budget_profit = df_sim.loc[mask_budget, 'profit'].sum()
    original_total = df_sim['profit'].sum()
    
    conversion_multiplier = (1.0 / 0.6) - 1
    profit_increase = original_budget_profit * (conversion_rate / 100) * conversion_multiplier
    
    new_total = original_total + profit_increase
    
    col1, col2 = st.columns(2)
    col1.metric("Базовая общая прибыль", f"${original_total:,.0f}")
    col2.metric("Расчетная общая прибыль", f"${new_total:,.0f}", f"+${profit_increase:,.0f}")

    st.markdown("### Сравнение структуры прибыли по сегментам (До / После)")
    
    reg_before = df.groupby('segment')['profit'].sum().reset_index()
    reg_before['Status'] = 'Текущая модель'
    
    reg_after = reg_before.copy()
    profit_shifted = original_budget_profit * (conversion_rate / 100)
    
    reg_after.loc[reg_after['segment'] == 'Budget', 'profit'] -= profit_shifted
    reg_after.loc[reg_after['segment'] == 'Standard', 'profit'] += profit_shifted + profit_increase
    reg_after['Status'] = 'Прогнозная модель'
    
    compare_df = pd.concat([reg_before, reg_after])
    fig = px.bar(compare_df, x='Status', y='profit', color='segment', barmode='group', title='Изменение распределения прибыли')
    st.plotly_chart(fig, use_container_width=True)

def render_recommendations(df):
    st.title("Шаг 6: Выводы и рекомендации")
    st.markdown("""
    **Аналитические выводы:**
    1. Сегмент **Budget** характеризуется наименьшими показателями финансовой прибыли при стабильно низком уровне удовлетворенности.
    2. Наиболее критичная ситуация наблюдается в категории Electronics по сегменту Budget (удовлетворенность < 3.0).
    3. Данная категория клиентов имеет минимальное влияние на итоговую прибыль.
    
    **Предлагаемые меры:**
    * Скорректировать ценовую и маркетинговую политику с целью сокращения доли сегмента Budget в обороте компании.
    * Стимулировать переход чувствительных к цене клиентов в сегмент Standard.
    * Рассмотреть сокращение ассортимента наиболее дешевых позиций в категории Electronics.
    """)
    
    summary_df = df.groupby('segment').agg({
        'revenue': 'sum', 
        'profit': 'sum', 
        'units_sold': 'sum',
        'customer_satisfaction': 'mean'
    }).reset_index().sort_values('profit', ascending=False)
    
    st.dataframe(summary_df.style.format({
        'revenue': '${:,.0f}', 
        'profit': '${:,.0f}', 
        'units_sold': '{:,.0f}',
        'customer_satisfaction': '{:.2f}'
    }), use_container_width=True)

def main():
    df_raw = load_data()
    
    if 'step' not in st.session_state:
        st.session_state.step = 0

    steps = ["Общая динамика", "Проблемные зоны", "Оценка вклада", "Матрица лояльности", "Моделирование", "Рекомендации"]
    
    with st.sidebar:
        st.header("Навигация")
        step_choice = st.radio("Выберите шаг", steps, index=st.session_state.step)
        st.session_state.step = steps.index(step_choice)
        
        st.header("Фильтры")
        all_cats = df_raw['category'].unique()
        all_regs = df_raw['region'].unique()
        selected_cat = st.multiselect("Категория", all_cats, default=all_cats)
        selected_reg = st.multiselect("Регион", all_regs, default=all_regs)
    
    df_filtered = df_raw[df_raw['category'].isin(selected_cat) & df_raw['region'].isin(selected_reg)]
    
    steps_funcs = [render_overview, render_anomaly, render_segments, render_cause, render_solution, render_recommendations]
    
    steps_funcs[st.session_state.step](df_filtered)

    st.divider()
    cols = st.columns([1, 8, 1])
    if st.session_state.step > 0:
        if cols[0].button("Назад"):
            st.session_state.step -= 1
            st.rerun()
    if st.session_state.step < len(steps) - 1:
        if cols[2].button("Далее"):
            st.session_state.step += 1
            st.rerun()

if __name__ == "__main__":
    main()