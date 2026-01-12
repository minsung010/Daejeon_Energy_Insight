import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from sqlalchemy import create_engine
import oracledb
from geopy.distance import geodesic
import requests
import dash.dependencies

# ==============================================================================
# 0. DB 설정 및 데이터 로드 (DB 연결 실패 시 임시 데이터 사용)
# ==============================================================================

DB_CONFIG = {
    'user': 'daejeon',
    'password': 'daejeon',
    'host': '192.168.0.2',
    'port': 1521,
    'sid': 'xe'
}
JOIN_KEY = 'MATCH_KEY'
BUILDING_INFO_TABLE = 'building_master'
ENERGY_USAGE_TABLE = 'energy_usage'
CURRENT_YEAR = 2025
KAKAO_API_KEY = "API_KEY"
try:
    oracledb.init_oracle_client(lib_dir=None, config_dir=None)
except Exception:
    pass


def search_query_kakao(query):
    address_url = "https://dapi.kakao.com/v2/local/search/address.json"
    keyword_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query}
    try:
        response = requests.get(address_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data['documents']:
            first_doc = data['documents'][0]
            lon = float(first_doc['x'])
            lat = float(first_doc['y'])
            full_address = (
                    first_doc.get('road_address', {}).get('address_name')
                    or first_doc.get('address', {}).get('address_name')
                    or query
            )
            return lat, lon, full_address, "주소 검색 성공"
    except requests.exceptions.RequestException:
        pass
    try:
        response = requests.get(keyword_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data['documents']:
            first_doc = data['documents'][0]
            lon = float(first_doc['x'])
            lat = float(first_doc['y'])
            place_name = first_doc.get('place_name', query)
            address_name = first_doc.get('address_name', '')
            full_address = f"{place_name} ({address_name})"
            return lat, lon, full_address, "키워드 검색 성공"
    except requests.exceptions.RequestException:
        pass
    return None, None, f"검색 결과 없음 ({query})", "전체 실패"


def load_data_from_db():
    print("DB에 연결하여 데이터 로드 및 병합 중...")
    try:
        engine = create_engine(
            f"oracle+oracledb://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['sid']}"
        )
        query_building = f"""
            SELECT {JOIN_KEY}, BILD_PRPOS, GRFA, BULD_SPANU_NUM, GU_NAME, LEGALDONG, LATITUDE, LONGITUDE, LOCATION, USE_APRV_Y 
            FROM {BUILDING_INFO_TABLE.upper()}
        """
        df_building = pd.read_sql(query_building, engine)
        query_energy = f"""
            SELECT {JOIN_KEY}, DATE_KEY, USE_ELECTRIC, USE_GAS, TOE_ELECTRIC, TOE_GAS, CARBON_ELECTRIC, CARBON_GAS
            FROM {ENERGY_USAGE_TABLE.upper()}
        """
        df_energy = pd.read_sql(query_energy, engine)
        df_building.columns = df_building.columns.str.lower()
        df_energy.columns = df_energy.columns.str.lower()
        df_merged = pd.merge(df_building, df_energy, on=JOIN_KEY.lower(), how='inner')
        if df_merged.empty:
            raise ValueError("DB에서 데이터를 로드했지만, 병합된 DataFrame이 비어있습니다.")
        df_merged.columns = df_merged.columns.str.upper()
        return df_merged
    except Exception as e:
        print(f"DB 연결 또는 쿼리 실행에 실패했습니다.")
        print(f"Error: {e}")
        print("⚠️ DB 연결 실패: 임시 데이터를 사용하여 실행합니다.")
        data = {
            'match_key': ['서구 둔산동 1-1', '중구 선화동 2-2', '서구 월평동 3-3', '동구 가양동 4-4', '유성구 봉명동 5-5',
                          '대덕구 오정동 6-6', '유성구 궁동 7-7', '서구 둔산동 8-8', '중구 선화동 9-9', '유성구 봉명동 10-10'],
            'bild_prpos': ['공동주택', '단독주택', '공동주택', '기타', '단독주택', '공동주택', '단독주택', '공동주택', '단독주택', '공동주택'],
            'grfa': [100, 50, 150, 200, 80, 120, 60, 110, 90, 130],
            'use_aprv_y': ['2024', '2021', '2022', '2023', '2024', '2022', '2021', '2023', '2024', '2022'],
            'gu_name': ['서구', '중구', '서구', '동구', '유성구', '대덕구', '유성구', '서구', '중구', '유성구'],
            'legaldong': ['둔산동', '선화동', '월평동', '가양동', '봉명동', '오정동', '궁동', '둔산동', '선화동', '봉명동'],
            'latitude': [36.350, 36.330, 36.351, 36.340, 36.360, 36.370, 36.370, 36.350, 36.331, 36.362],
            'longitude': [127.380, 127.420, 127.350, 127.430, 127.340, 127.370, 127.360, 127.370, 127.421, 127.341],
            'location': ['NORMAL', 'NORMAL', 'MISSING', 'NORMAL', 'NORMAL', 'MISSING', 'NORMAL', 'NORMAL', 'NORMAL',
                         'NORMAL'],
            'date_key': ['202101', '202202', '202301', '202402', '202103', '202203', '202304', '202404', '202301',
                         '202402',
                         '202111', '202212', '202305', '202406', '202501', '202502', '202503', '202504'],
            'use_electric': [100, 50, 120, 200, 150, 90, 70, 130, 60, 140, 110, 100, 150, 200, 100, 150, 200, 250],
            'use_gas': [50, 20, 60, 100, 75, 45, 35, 65, 30, 70, 55, 50, 75, 100, 50, 75, 100, 125],
            'toe_electric': [1, 0.5, 1.2, 2, 1.5, 0.9, 0.7, 1.3, 0.6, 1.4, 1.1, 1.0, 1.5, 2.0, 1.0, 1.5, 2.0, 2.5],
            'toe_gas': [0.5, 0.2, 0.6, 1, 0.75, 0.45, 0.35, 0.65, 0.3, 0.7, 0.55, 0.5, 0.75, 1.0, 0.5, 0.75, 1.0, 1.25],
            'carbon_electric': [50, 25, 60, 100, 75, 45, 35, 65, 30, 70, 55, 50, 75, 100, 50, 75, 100, 125],
            'carbon_gas': [25, 10, 30, 50, 38, 23, 18, 33, 15, 35, 28, 25, 38, 50, 25, 38, 50, 63],
        }
        num_rows = len(data['match_key'])
        for key in data:
            if key != 'date_key' and len(data[key]) < len(data['date_key']):
                data[key] = (data[key] * (len(data['date_key']) // len(data[key]))) + data[key][
                    :len(data['date_key']) % len(data[key])]

        df = pd.DataFrame(data)
        df.columns = df.columns.str.upper()
        return df


df = load_data_from_db()

# ==============================================================================
# 1. 데이터 전처리 및 옵션 생성
# ==============================================================================

cols_to_use = ['MATCH_KEY', 'BILD_PRPOS', 'GRFA', 'USE_APRV_Y', 'GU_NAME',
               'LEGALDONG', 'LATITUDE', 'LONGITUDE', 'LOCATION', 'DATE_KEY',
               'USE_ELECTRIC', 'USE_GAS', 'TOE_ELECTRIC', 'TOE_GAS',
               'CARBON_ELECTRIC', 'CARBON_GAS']
df_data = df[[c for c in cols_to_use if c in df.columns]].copy()
if 'DATE_KEY' in df_data.columns and not pd.api.types.is_string_dtype(df_data['DATE_KEY']):
    df_data['DATE_KEY'] = df_data['DATE_KEY'].astype(str).str.split('.').str[0]
if 'DATE_KEY' in df_data.columns:
    df_data['YEAR'] = df_data['DATE_KEY'].str[:4].astype(int)
    df_data['MONTH'] = df_data['DATE_KEY'].str[4:].astype(int)
else:
    df_data['YEAR'] = CURRENT_YEAR
    df_data['MONTH'] = 1
df_data['HOUSE_TYPE'] = np.where(df_data['BILD_PRPOS'].str.contains('단독주택', na=False), '단독주택',
                                 np.where(df_data['BILD_PRPOS'].str.contains('공동주택', na=False), '공동주택', '기타'))
df_data = df_data[df_data['HOUSE_TYPE'].isin(['단독주택', '공동주택'])].copy()
BUILD_YEAR_COL = 'USE_APRV_Y'
if BUILD_YEAR_COL in df_data.columns:
    df_data['TEMP_DATE'] = pd.to_datetime(df_data[BUILD_YEAR_COL], format='%y/%m/%d', errors='coerce')
    df_data['EXTRACTED_YEAR'] = df_data['TEMP_DATE'].dt.year
    df_data[BUILD_YEAR_COL] = df_data['EXTRACTED_YEAR'].fillna(CURRENT_YEAR).astype(int)
    df_data.drop(columns=['TEMP_DATE', 'EXTRACTED_YEAR'], inplace=True, errors='ignore')
else:
    df_data[BUILD_YEAR_COL] = CURRENT_YEAR
df_data['AGE'] = CURRENT_YEAR - df_data[BUILD_YEAR_COL]


def get_age_group(age):
    if age < 0:
        return '오류'
    elif 0 <= age <= 9:
        return '0~9년'
    elif 10 <= age <= 20:
        return '10~20년'
    elif 21 <= age <= 30:
        return '20~30년'
    else:
        return '30년이상'


df_data['AGE_GROUP'] = df_data['AGE'].apply(get_age_group)
AGE_GROUPS = ['0~9년', '10~20년', '20~30년', '30년이상']
ENERGY_COLS = ['USE_ELECTRIC', 'USE_GAS', 'TOE_ELECTRIC', 'TOE_GAS', 'CARBON_ELECTRIC', 'CARBON_GAS']
ENERGY_LABELS = {
    'USE_ELECTRIC': '전기 사용량', 'USE_GAS': '가스 사용량',
    'TOE_ELECTRIC': '전기 TOE', 'TOE_GAS': '가스 TOE',
    'CARBON_ELECTRIC': '전기 탄소배출량', 'CARBON_GAS': '가스 탄소배출량'
}
ENERGY_UNIT_DETAILS = {
    'USE_ELECTRIC': {'unit': 'kWh', 'type': '사용량'},
    'USE_GAS': {'unit': 'kWh', 'type': '사용량'},
    'TOE_ELECTRIC': {'unit': 'TOE', 'type': 'TOE'},
    'TOE_GAS': {'unit': 'TOE', 'type': 'TOE'},
    'CARBON_ELECTRIC': {'unit': 'tCO2', 'type': '탄소배출량'},
    'CARBON_GAS': {'unit': 'tCO2', 'type': '탄소배출량'}
}
df_data['GRFA'] = df_data['GRFA'].replace(0, np.nan)
df_data.loc[df_data['GRFA'] < 30, 'GRFA'] = np.nan
df_data.loc[df_data['GRFA'] > 50000, 'GRFA'] = np.nan

for col in ENERGY_COLS:
    # df_data.loc[:, f'PER_GRFA_{col}'] = df_data[col] / df_data['GRFA'].replace(0, np.nan)
    df_data[f'PER_GRFA_{col}'] = df_data[col] / df_data['GRFA']
    ENERGY_LABELS[f'PER_GRFA_{col}'] = f'연면적당 {ENERGY_LABELS[col]}'
GU_OPTIONS = sorted(df_data['GU_NAME'].unique().tolist())
gu_to_dong_map = (
    df_data.groupby('GU_NAME')['LEGALDONG']
    .apply(lambda x: sorted(x.unique().tolist()))
    .to_dict()
)
initial_gu_name = GU_OPTIONS[0] if GU_OPTIONS else '서구'
initial_dong_choices = ['전체 동 평균']
if initial_gu_name:
    initial_dong_choices += gu_to_dong_map.get(initial_gu_name, [])
HOUSE_OPTIONS = ['전체 평균'] + sorted(df_data['HOUSE_TYPE'].unique().tolist())
METRIC_OPTIONS = {v: k for k, v in ENERGY_LABELS.items() if not k.startswith('PER_GRFA_')}
YEAR_OPTIONS_SINGLE = sorted(df_data['YEAR'].unique().astype(str).tolist())
YEAR_OPTIONS_MULTI = ['전체 평균'] + [y for y in YEAR_OPTIONS_SINGLE if int(y) >= 2021]
YEAR_OPTIONS_MULTI = sorted(list(set(YEAR_OPTIONS_MULTI)), key=lambda x: (x != '전체 평균', x))
MONTH_OPTIONS = list(range(1, 13))
HOUSE_OPTIONS_DASH = [{'label': i, 'value': i} for i in HOUSE_OPTIONS]
METRIC_OPTIONS_DASH = [{'label': i, 'value': i} for i in METRIC_OPTIONS.keys()]
YEAR_OPTIONS_SINGLE_DASH = [{'label': i, 'value': i} for i in YEAR_OPTIONS_SINGLE + ['전체 평균']]
YEAR_OPTIONS_SINGLE_DASH = sorted(YEAR_OPTIONS_SINGLE_DASH, key=lambda x: (x['value'] != '전체 평균', x['value']))
MONTH_OPTIONS_DASH = [{'label': i, 'value': i} for i in MONTH_OPTIONS]
GU_OPTIONS_DASH = [{'label': i, 'value': i} for i in GU_OPTIONS]
GRAPH_TYPE_OPTIONS = [
    {'label': '선 그래프', 'value': 'line'},
    {'label': '수직 막대', 'value': 'bar'},
]


# ==============================================================================
# 2. Plotly 그래프 생성 함수
# ==============================================================================

def plot_interactive_gradio_1_2(house_type, energy_metric_name, year_selection_list, start_month, end_month,
                                graph_type):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    plot_func = px.line if graph_type == 'line' else px.bar
    plot_kwargs = {'barmode': 'group'} if graph_type == 'bar' else {}
    if house_type == '전체 평균':
        df_filtered = df_data.copy()
        plot_title_prefix = '전체 주택 평균'
    else:
        df_filtered = df_data[df_data['HOUSE_TYPE'] == house_type].copy()
        plot_title_prefix = f'{house_type} 평균'
    if start_month < 1 or end_month > 12 or start_month > end_month:
        df_monthly_filtered = df_filtered.copy()
        month_title = "전체 월"
    else:
        df_monthly_filtered = df_filtered[
            (df_filtered['MONTH'] >= start_month) & (df_filtered['MONTH'] <= end_month)].copy()
        month_title = f"{start_month}월 ~ {end_month}월"
    if df_monthly_filtered.empty:
        return [px.line(title="데이터가 없습니다."), px.bar(title="데이터가 없습니다.")]
    base_metric = energy_metric_key
    all_line_data = []
    if not year_selection_list:
        year_selection_list = ['전체 평균']
    for year_sel in year_selection_list:
        if year_sel == '전체 평균':
            monthly_line_data = df_monthly_filtered.groupby('MONTH')[base_metric].mean().reset_index()
            monthly_line_data['YEAR_GROUP'] = '전체 년도 평균'
        else:
            year_int = int(year_sel)
            df_year = df_monthly_filtered[df_monthly_filtered['YEAR'] == year_int]
            monthly_line_data = df_year.groupby('MONTH')[base_metric].mean().reset_index()
            monthly_line_data['YEAR_GROUP'] = year_sel
        monthly_line_data.rename(columns={base_metric: 'VALUE'}, inplace=True)
        all_line_data.append(monthly_line_data[['MONTH', 'VALUE', 'YEAR_GROUP']])
    df_combined_line = pd.concat(all_line_data, ignore_index=True)
    y_axis_title_line = f'평균 {unit_type} ({unit})'
    fig1 = plot_func(df_combined_line,
                     x='MONTH', y='VALUE', color='YEAR_GROUP',
                     title=f'{plot_title_prefix} - {month_title} 월별 {energy_metric_name}',
                     labels={'MONTH': '월', 'VALUE': y_axis_title_line, 'YEAR_GROUP': '년도'},
                     template='plotly_white',
                     color_discrete_sequence=px.colors.qualitative.Dark2,
                     **plot_kwargs)
    fig1.update_xaxes(tickvals=list(range(start_month, end_month + 1)))
    per_grfa_metric = f'PER_GRFA_{energy_metric_key}'
    all_bar_data = []
    for year_sel in year_selection_list:
        df_plot_per_grfa = df_monthly_filtered.dropna(subset=[per_grfa_metric])
        if year_sel == '전체 평균':
            monthly_bar_data = df_plot_per_grfa.groupby('MONTH')[per_grfa_metric].mean().reset_index()
            monthly_bar_data['YEAR_GROUP'] = '전체 년도 평균'
        else:
            year_int = int(year_sel)
            df_year = df_plot_per_grfa[df_plot_per_grfa['YEAR'] == year_int]
            monthly_bar_data = df_year.groupby('MONTH')[per_grfa_metric].mean().reset_index()
            monthly_bar_data['YEAR_GROUP'] = year_sel
        monthly_bar_data.rename(columns={per_grfa_metric: 'VALUE'}, inplace=True)
        all_bar_data.append(monthly_bar_data[['MONTH', 'VALUE', 'YEAR_GROUP']])
    df_combined_bar = pd.concat(all_bar_data, ignore_index=True)
    y_axis_title = f'연면적당 평균 {unit_type} ({unit}/m²)'
    fig2 = plot_func(df_combined_bar,
                     x='MONTH', y='VALUE', color='YEAR_GROUP',
                     title=f'{plot_title_prefix} - {month_title} 월별 {ENERGY_LABELS[per_grfa_metric]}',
                     labels={'MONTH': '월', 'VALUE': y_axis_title, 'YEAR_GROUP': '년도'},
                     template='plotly_white',
                     color_discrete_sequence=px.colors.qualitative.Dark2,
                     **plot_kwargs)
    fig2.update_xaxes(tickvals=list(range(start_month, end_month + 1)))
    return [fig1, fig2]


def plot_gu_comparison(house_type, energy_metric_name, gu_selection_list, year_selection, start_month, end_month,
                       graph_type):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    plot_func = px.line if graph_type == 'line' else px.bar
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    if not gu_selection_list: return px.line(title="3. 비교할 '구'를 하나 이상 선택해주세요.")
    if house_type == '전체 평균':
        df_plot = df_data.copy()
        plot_title_prefix = '전체 주택'
    else:
        df_plot = df_data[df_data['HOUSE_TYPE'] == house_type].copy()
        plot_title_prefix = f'{house_type}'
    df_plot = df_plot[df_plot['GU_NAME'].isin(gu_selection_list)].copy()
    if year_selection != '전체 평균':
        year_int = int(year_selection)
        df_plot = df_plot[df_plot['YEAR'] == year_int].copy()
        year_label = f'{year_selection}년'
    else:
        year_label = '전체 년도'
    if start_month < 1 or end_month > 12 or start_month > end_month:
        month_title = "전체 월"
    else:
        df_plot = df_plot[(df_plot['MONTH'] >= start_month) & (df_plot['MONTH'] <= end_month)].copy()
        month_title = f"{start_month}월 ~ {end_month}월"
    if df_plot.empty: return px.line(title=f"3. 선택된 지역에 해당 데이터가 없습니다.")
    base_metric = energy_metric_key
    monthly_data = df_plot.groupby(['GU_NAME', 'MONTH'])[base_metric].mean().reset_index()
    y_axis_title = f'평균 {unit_type} ({unit})'
    fig = plot_func(monthly_data, x='MONTH', y=base_metric, color='GU_NAME',
                    title=f'{plot_title_prefix} - 구별 {year_label} {month_title} {energy_metric_name} 추이',
                    labels={'MONTH': '월', base_metric: y_axis_title, 'GU_NAME': '구'},
                    template='plotly_white', height=350)
    if graph_type == 'bar':
        fig.update_layout(barmode='group')
    fig.update_xaxes(tickvals=list(range(start_month, end_month + 1)))

    return fig


def plot_dong_comparison(house_type, energy_metric_name, gu_name, dong_selection_list, year_selection, start_month,
                         end_month, graph_type):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    plot_func = px.line if graph_type == 'line' else px.bar
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    if not gu_name: return px.line(title="3-1. '구'를 선택해주세요.")
    if not dong_selection_list: return px.line(title="3-1. 비교할 '동'을 하나 이상 선택해주세요.")
    if house_type == '전체 평균':
        df_plot = df_data.copy()
        plot_title_prefix = '전체 주택'
    else:
        df_plot = df_data[df_data['HOUSE_TYPE'] == house_type].copy()
        plot_title_prefix = f'{house_type}'
    df_plot = df_plot[df_plot['GU_NAME'] == gu_name].copy()
    if year_selection != '전체 평균':
        year_int = int(year_selection)
        df_plot = df_plot[df_plot['YEAR'] == year_int].copy()
        year_label = f'{year_selection}년'
    else:
        year_label = '전체 년도'
    if start_month < 1 or end_month > 12 or start_month > end_month:
        month_title = "전체 월"
    else:
        df_plot = df_plot[(df_plot['MONTH'] >= start_month) & (df_plot['MONTH'] <= end_month)].copy()
        month_title = f"{start_month}월 ~ {end_month}월"
    if df_plot.empty: return px.line(title=f"3-1. {gu_name} 내 해당 기간/유형 데이터가 없습니다.")
    base_metric = energy_metric_key
    monthly_data_list = []
    dong_list_for_filter = dong_selection_list.copy()
    if '전체 동 평균' in dong_list_for_filter:
        df_all_dong_avg = df_plot.groupby(['MONTH'])[base_metric].mean().reset_index()
        df_all_dong_avg['LEGALDONG'] = '전체 동 평균'
        monthly_data_list.append(df_all_dong_avg)
        dong_list_for_filter.remove('전체 동 평균')
    if dong_list_for_filter:
        df_individual_dong = df_plot[df_plot['LEGALDONG'].isin(dong_list_for_filter)].copy()
        if not df_individual_dong.empty:
            df_dong_avg = df_individual_dong.groupby(['LEGALDONG', 'MONTH'])[base_metric].mean().reset_index()
            monthly_data_list.append(df_dong_avg)
    if not monthly_data_list: return px.line(title=f"3-1. {gu_name} 내 선택된 동에 해당 데이터가 없습니다.")
    monthly_data = pd.concat(monthly_data_list, ignore_index=True)
    all_selected_dongs = dong_selection_list
    y_axis_title = f'평균 {unit_type} ({unit})'
    fig = plot_func(monthly_data, x='MONTH', y=base_metric, color='LEGALDONG',
                    title=f'{plot_title_prefix} - {gu_name} 내 동별  {year_label} {month_title} {energy_metric_name} 추이',
                    labels={'MONTH': '월', base_metric: y_axis_title, 'LEGALDONG': '동/평균'},
                    template='plotly_white', height=350)
    if graph_type == 'bar':
        fig.update_layout(barmode='group')
    fig.update_xaxes(tickvals=list(range(start_month, end_month + 1)))

    return fig


def plot_age_group_usage(energy_metric_name, house_type):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    if house_type == '전체 평균':
        df_filtered = df_data.copy()
        title_prefix = '전체 주택'
    else:
        df_filtered = df_data[df_data['HOUSE_TYPE'] == house_type].copy()
        title_prefix = f'{house_type}'
    df_plot = df_filtered.dropna(subset=['AGE_GROUP', energy_metric_key])
    if df_plot.empty: return px.bar(title="4. 데이터가 없습니다.")
    df_age_avg = df_plot.groupby('AGE_GROUP')[energy_metric_key].mean().reset_index()
    df_age_avg['AGE_GROUP'] = pd.Categorical(df_age_avg['AGE_GROUP'], categories=AGE_GROUPS, ordered=True)
    df_age_avg = df_age_avg.sort_values('AGE_GROUP')
    y_axis_title = f'평균 {unit_type} ({unit})'
    fig = px.bar(df_age_avg, x='AGE_GROUP', y=energy_metric_key,
                 title=f'{title_prefix} - 노후도 그룹별 평균 {energy_metric_name} 비교',
                 labels={'AGE_GROUP': '노후도 그룹', energy_metric_key: y_axis_title},
                 template='plotly_white', color_discrete_sequence=['#4CAF50'])
    return fig


def plot_age_group_per_grfa(energy_metric_name, house_type):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    per_grfa_metric = f'PER_GRFA_{energy_metric_key}'
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    if house_type == '전체 평균':
        df_filtered = df_data.copy()
        title_prefix = '전체 주택'
    else:
        df_filtered = df_data[df_data['HOUSE_TYPE'] == house_type].copy()
        title_prefix = f'{house_type}'
    df_plot = df_filtered.dropna(subset=['AGE_GROUP', per_grfa_metric])
    if df_plot.empty: return px.bar(title="5. 데이터가 없습니다.")
    df_age_avg = df_plot.groupby('AGE_GROUP')[per_grfa_metric].mean().reset_index()
    df_age_avg['AGE_GROUP'] = pd.Categorical(df_age_avg['AGE_GROUP'], categories=AGE_GROUPS, ordered=True)
    df_age_avg = df_age_avg.sort_values('AGE_GROUP')
    y_axis_title = f'연면적당 평균 {unit_type} ({unit}/m²)'
    fig = px.bar(df_age_avg, x='AGE_GROUP', y=per_grfa_metric,
                 title=f'{title_prefix} - 노후도 그룹별 평균 {ENERGY_LABELS[per_grfa_metric]} 비교',
                 labels={'AGE_GROUP': '노후도 그룹', per_grfa_metric: y_axis_title},
                 template='plotly_white', color_discrete_sequence=['#8BC34A'])

    return fig


def plot_neighborhood_comparison(target_match_key, energy_metric_name):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    base_metric = energy_metric_key
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    target_match_key = str(target_match_key).strip()
    if not target_match_key: return px.bar(title=f"주소 검색 후 비교할 건물을 선택해주세요.", height=400)
    target_building = df_data[df_data[JOIN_KEY] == target_match_key]
    if target_building.empty: return px.bar(title=f"주소: {target_match_key} 에 해당하는 건물 데이터가 없습니다.")
    target_lat = target_building['LATITUDE'].mean()
    target_lon = target_building['LONGITUDE'].mean()
    target_usage = target_building[base_metric].mean()
    if pd.isna(target_lat) or pd.isna(target_lon) or abs(target_lat) > 90 or abs(target_lon) > 180:
        return px.bar(title=f"6. 대상 건물 '{target_match_key}'의 유효한 위/경도 정보가 없어 비교할 수 없습니다.")

    def calculate_distance(row, target_coords):
        if row[JOIN_KEY] == target_match_key: return np.inf
        if pd.isna(row['LATITUDE']) or pd.isna(row['LONGITUDE']): return np.inf
        if abs(row['LATITUDE']) > 90 or abs(row['LONGITUDE']) > 180: return np.inf
        return geodesic(target_coords, (row['LATITUDE'], row['LONGITUDE'])).m

    df_data['DISTANCE_M'] = df_data.apply(
        lambda row: calculate_distance(row, (target_lat, target_lon)), axis=1
    )
    df_neighborhood = df_data[(df_data['DISTANCE_M'] <= 100)].copy()
    neighborhood_avg = df_neighborhood.drop_duplicates(subset=[JOIN_KEY])[
        base_metric].mean() if not df_neighborhood.empty else 0
    df_result = pd.DataFrame({
        'Category': ['선택 건물', '반경 100m 평균'],
        'Usage': [target_usage, neighborhood_avg],
        'Count': [1, len(df_neighborhood.drop_duplicates(subset=[JOIN_KEY]))]
    })
    y_axis_title = f'평균 {unit_type} ({unit})'
    fig = px.bar(df_result, x='Category', y='Usage',
                 title=f"건물 주소 '{target_match_key}' vs. 반경 100m 건물 평균 ({energy_metric_name})",
                 labels={'Category': '비교 대상', 'Usage': y_axis_title},
                 template='plotly_white', color='Category', color_discrete_sequence=['#2E7D32', '#66BB6A'])
    fig.update_layout(height=400,bargap=0.1)

    return fig


def plot_similarity_comparison(target_match_key, energy_metric_name):
    energy_metric_key = METRIC_OPTIONS[energy_metric_name]
    base_metric = energy_metric_key
    unit = ENERGY_UNIT_DETAILS[energy_metric_key]['unit']
    unit_type = ENERGY_UNIT_DETAILS[energy_metric_key]['type']
    target_match_key = str(target_match_key).strip()
    if not target_match_key: return px.bar(title=f"주소 검색 후 비교할 건물을 선택해주세요.", height=400)
    target_building = df_data[df_data[JOIN_KEY] == target_match_key]
    if target_building.empty: return px.bar(title=f"주소: {target_match_key} 에 해당하는 건물 데이터가 없습니다.")
    target_grfa = target_building['GRFA'].mean()
    target_age = target_building['AGE'].mean()
    target_usage = target_building[base_metric].mean()
    grfa_min, grfa_max = target_grfa * 0.9, target_grfa * 1.1
    age_min, age_max = target_age - 5, target_age + 5
    df_similar = df_data[
        (df_data['GRFA'] >= grfa_min) & (df_data['GRFA'] <= grfa_max) &
        (df_data['AGE'] >= age_min) & (df_data['AGE'] <= age_max) &
        (df_data[JOIN_KEY] != target_match_key)
        ].copy()
    similar_avg = df_similar.drop_duplicates(subset=[JOIN_KEY])[base_metric].mean() if not df_similar.empty else 0
    df_result = pd.DataFrame({
        'Category': ['선택 건물', '유사 조건 평균'],
        'Usage': [target_usage, similar_avg],
        'Count': [1, len(df_similar.drop_duplicates(subset=[JOIN_KEY]))]
    })
    y_axis_title = f'평균 {unit_type} ({unit})'
    fig = px.bar(df_result, x='Category', y='Usage',
                 title=f"건물 주소 '{target_match_key}' vs. 연면적/노후도 유사 건물 평균 ({energy_metric_name})",
                 labels={'Category': '비교 대상', 'Usage': y_axis_title},
                 template='plotly_white', color='Category', color_discrete_sequence=['#388E3C', '#A5D6A7'])
    fig.update_layout(height=400,bargap=0.1)  # 0~1 사이 값, 작을수록 막대 좁아짐)
    return fig


# ==============================================================================
# 3. Dash 앱 초기화 및 통합 레이아웃 정의
# ==============================================================================
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.title = "에너지 데이터 대시보드"

app.layout = html.Div(style={'padding': '15px'}, children=[

    # 🌟 모달 상태 관리용 Store 추가
    dcc.Store(id='year-modal-open', data=False),
    dcc.Store(id='gu-modal-open', data=False),
    dcc.Store(id='dong-modal-open', data=False),
    dcc.Interval(id='click-detector', interval=100, n_intervals=0),  # 클릭 감지용

    html.H2('에너지 데이터 대시보드', style={'textAlign': 'center', 'marginBottom': '30px'}),

    # --- 1. 1/2번 그래프 영역 ---
    html.H3('전체 추이 분석', style={'textAlign': 'center', 'marginTop': '15px'}),
    html.Div(id='filters-1-2', style={'padding': '10px'}, children=[
        html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
            html.Div(style={'width': '20%'}, children=[html.Label("주택 유형"),
                                                       dcc.Dropdown(id='house-type-1-2', options=HOUSE_OPTIONS_DASH,
                                                                    value='전체 평균', clearable=False)]),
            html.Div(style={'width': '20%'}, children=[html.Label("에너지 지표"),
                                                       dcc.Dropdown(id='energy-metric-1-2', options=METRIC_OPTIONS_DASH,
                                                                    value='전기 사용량', clearable=False)]),
            html.Div(style={'width': '20%'}, children=[html.Label("그래프 종류"),
                                                       dcc.Dropdown(id='graph-type-1-2', options=GRAPH_TYPE_OPTIONS,
                                                                    value='line', clearable=False)]),

            # 🌟 년도 선택 - 드롭다운 스타일 모달
            html.Div(style={'width': '30%'}, children=[
                html.Label("년도 선택"),
                html.Div(className='modal-wrapper', children=[
                    html.Button("년도 선택", id="open-year-modal-btn"),
                    html.Div(
                        id="year-modal-container",
                        style={"display": "none"},
                        children=[
                            html.Div(id="year-modal-box",
                                className="modal-box",
                                children=[
                                    html.H4("년도 선택"),
                                    dcc.Checklist(
                                        id='year-selection-checklist',
                                        options=[{'label': i, 'value': i} for i in YEAR_OPTIONS_MULTI],
                                        value=['전체 평균'],
                                        className='button-checklist'
                                    ),
                                    html.Button("닫기", id="close-year-modal-btn", n_clicks=0)
                                ]
                            )
                        ]
                    ),
                ]),
                dcc.Store(id='selected-years-store'),
            ])

        ]),
        html.Div(style={'display': 'flex', 'gap': '10px', 'marginTop': '10px'}, children=[
            html.Div(style={'width': '20%'}, children=[html.Label("시작 월"),
                                                       dcc.Dropdown(id='start-month-1-2', options=MONTH_OPTIONS_DASH,
                                                                    value=1, clearable=False)]),
            html.Div(style={'width': '20%'}, children=[html.Label("종료 월"),
                                                       dcc.Dropdown(id='end-month-1-2', options=MONTH_OPTIONS_DASH,
                                                                    value=12, clearable=False)]),
        ]),
    ]),
    dcc.Graph(id='plot-1-output', style={'width': '100%', 'height': '350px'}),
    dcc.Graph(id='plot-2-output', style={'width': '100%', 'marginTop': '20px', 'height': '350px'}),

    html.Hr(style={'margin': '50px 0'}),

    # --- 2. 3번 그래프 영역 (구별 비교 추이) ---
    html.H3('구별 상세 추이 분석', style={'textAlign': 'center'}),
    html.Div(id='filters-3', style={'padding': '10px'}, children=[
        html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
            html.Div(style={'width': '18%'}, children=[html.Label("주택 유형"),
                                                       dcc.Dropdown(id='house-type-3', options=HOUSE_OPTIONS_DASH,
                                                                    value='전체 평균', clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("에너지 지표"),
                                                       dcc.Dropdown(id='energy-metric-3', options=METRIC_OPTIONS_DASH,
                                                                    value='전기 사용량', clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("그래프 종류"),
                                                       dcc.Dropdown(id='graph-type-3', options=GRAPH_TYPE_OPTIONS,
                                                                    value='line', clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("년도 선택"), dcc.Dropdown(id='year-selection-3',
                                                                                         options=YEAR_OPTIONS_SINGLE_DASH,
                                                                                         value='전체 평균',
                                                                                         clearable=False)]),
            # 🌟 구 선택 - 드롭다운 스타일 모달
            html.Div(style={'width': '18%', 'position': 'relative'}, children=[
                html.Label("구 선택"),
                html.Div(className='modal-wrapper', children=[
                    html.Button("구 선택", id="open-gu-modal-btn"),
                    html.Div(
                        id="gu-modal-container",
                        style={"display": "none"},
                        children=[
                            html.Div(id="gu-modal-box",
                                className="modal-box",
                                children=[
                                    html.H4("구 선택"),
                                    dcc.Checklist(
                                        id="gu-checklist-modal",
                                        options=GU_OPTIONS_DASH,
                                        value=[initial_gu_name],
                                        className="button-checklist"
                                    ),
                                    html.Button("닫기", id="close-gu-modal-btn", n_clicks=0)
                                ]
                            )
                        ]
                    ),
                ]),
                dcc.Store(id='selected-gu-store')
            ])

        ]),
        html.Div(style={'display': 'flex', 'gap': '10px', 'marginTop': '10px'}, children=[
            html.Div(style={'width': '18%'}, children=[html.Label("시작 월"),
                                                       dcc.Dropdown(id='start-month-3', options=MONTH_OPTIONS_DASH,
                                                                    value=1, clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("종료 월"),
                                                       dcc.Dropdown(id='end-month-3', options=MONTH_OPTIONS_DASH,
                                                                    value=12, clearable=False)]),
        ]),
    ]),
    dcc.Graph(id='plot-3-output', style={'marginTop': '20px', 'width': '100%', 'height': '380px'}),

    html.Hr(style={'margin': '50px 0'}),

    # --- 3. 3-1번 그래프 영역 (동별 비교 추이) ---
    html.H3('동별 상세 추이 분석', style={'textAlign': 'center'}),
    html.Div(id='filters-3-1', style={'padding': '10px'}, children=[
        html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
            html.Div(style={'width': '18%'}, children=[html.Label("주택 유형"),
                                                       dcc.Dropdown(id='house-type-3-1', options=HOUSE_OPTIONS_DASH,
                                                                    value='전체 평균', clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("에너지 지표"),
                                                       dcc.Dropdown(id='energy-metric-3-1', options=METRIC_OPTIONS_DASH,
                                                                    value='전기 사용량', clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("그래프 종류"),
                                                       dcc.Dropdown(id='graph-type-3-1', options=GRAPH_TYPE_OPTIONS,
                                                                    value='line', clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("년도 선택"), dcc.Dropdown(id='year-selection-3-1',
                                                                                         options=YEAR_OPTIONS_SINGLE_DASH,
                                                                                         value='전체 평균',
                                                                                         clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("구 선택"),
                                                       dcc.Dropdown(id='gu-dropdown-3-1', options=GU_OPTIONS_DASH,
                                                                    value=initial_gu_name, clearable=False)]),
            # 🌟 동 선택 - 드롭다운 스타일 모달
            html.Div(style={'width': '18%', 'position': 'relative'}, children=[
                html.Label("동 선택"),
                html.Div(className='modal-wrapper', children=[
                    html.Button("동 선택", id="open-dong-modal-btn"),
                    html.Div(
                        id="dong-modal-container",
                        style={"display": "none"},
                        children=[
                            html.Div(id="dong-modal-box",
                                className="modal-box",
                                children=[
                                    html.H4("동 선택"),
                                    dcc.Checklist(
                                        id='dong-checklist-3-1',
                                        options=[{'label': i, 'value': i} for i in initial_dong_choices],
                                        value=['전체 동 평균'],
                                        className='button-checklist'
                                    ),
                                    html.Button("닫기", id="close-dong-modal-btn", n_clicks=0)
                                ]
                            )
                        ]
                    ),
                ]),
                dcc.Store(id='selected-dong-store')
            ]),
        ]),
        html.Div(style={'display': 'flex', 'gap': '10px', 'marginTop': '10px'}, children=[
            html.Div(style={'width': '18%'}, children=[html.Label("시작 월"),
                                                       dcc.Dropdown(id='start-month-3-1', options=MONTH_OPTIONS_DASH,
                                                                    value=1, clearable=False)]),
            html.Div(style={'width': '18%'}, children=[html.Label("종료 월"),
                                                       dcc.Dropdown(id='end-month-3-1', options=MONTH_OPTIONS_DASH,
                                                                    value=12, clearable=False)]),
        ]),
    ]),
    dcc.Graph(id='plot-3-1-output', style={'marginTop': '20px', 'width': '100%', 'height': '380px'}),

    html.Hr(style={'margin': '50px 0', 'borderTop': '2px dashed #ccc'}),

    # --- 4. 4, 5번 그래프 영역 (노후도 분석) ---
    html.H2('노후도 그룹별 에너지 분석', style={'textAlign': 'center', 'marginBottom': '30px'}),

    html.Div(style={'display': 'flex', 'gap': '10px', 'padding': '10px', 'justifyContent': 'flex-start'}, children=[
        html.Div(style={'width': '20%'}, children=[
            html.Label("에너지 지표"),
            dcc.Dropdown(id='energy-metric-4-5', options=METRIC_OPTIONS_DASH, value='전기 사용량', clearable=False),
        ]),
        html.Div(style={'width': '20%'}, children=[
            html.Label("주택 유형"),
            dcc.Dropdown(id='house-type-4-5', options=HOUSE_OPTIONS_DASH, value='전체 평균', clearable=False),
        ]),
    ]),

    html.Div(style={'display': 'flex', 'marginTop': '20px', 'gap': '20px'}, children=[
        html.Div(style={'width': '50%'}, children=[
            dcc.Graph(id='plot-4-output', style={'height': '500px'})
        ]),
        html.Div(style={'width': '50%'}, children=[
            dcc.Graph(id='plot-5-output', style={'height': '500px'})
        ]),
    ]),

    html.Hr(style={'margin': '50px 0', 'borderTop': '2px dashed #ccc'}),

    # --- 5. 개별 건물 비교 분석 (벤치마킹) ---
    html.H2('개별 건물 비교 분석', style={'textAlign': 'center', 'marginBottom': '30px'}),

    html.Div(style={'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'marginBottom': '20px',
                    'backgroundColor': '#f9f9f9'}, children=[
        html.H4('대상 건물 주소 검색', style={'marginTop': '0', 'color': '#007bff'}),
        html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
            html.Div(style={'width': '50%'}, children=[
                html.Label("검색할 주소/장소명 입력"),
                dcc.Input(
                    id='search-address-input',
                    type='text',
                    placeholder='예: 대전시청 또는 대전광역시 서구 둔산동 123-4',
                    style={'width': '100%'}
                ),
            ]),
            html.Div(style={'width': '20%'}, children=[
                html.Label("검색 실행"),
                html.Button('주소/장소 검색', id='search-button', n_clicks=0,
                            style={'height': '38px', 'backgroundColor': '#8cd98c', 'color': '#000',
                                   'border': 'none', 'borderRadius': '4px', 'fontWeight': 'bold'}),
            ]),
        ]),
        html.Div(id='search-status-output', style={'marginTop': '10px', 'color': '#2E7D32', 'fontWeight': 'bold'}),
    ]),

    html.Div(style={'display': 'flex', 'gap': '10px', 'padding': '10px', 'justifyContent': 'flex-start'}, children=[
        html.Div(style={'width': '30%'}, children=[
            html.Label("대상 건물 주소"),
            dcc.Input(
                id='target-match-key',
                type='text',
                value='',
                disabled=True,
                debounce=True,
                placeholder='',
                style={'width': '100%'}
            ),
        ]),
        html.Div(style={'width': '20%'}, children=[
            html.Label("에너지 지표"),
            dcc.Dropdown(id='energy-metric-6-7', options=METRIC_OPTIONS_DASH, value='전기 사용량', clearable=False),
        ]),
    ]),

    html.H3('검색된 건물 반경 100m 건물 평균 비교', style={'marginTop': '30px'}),
    dcc.Loading(
        id="loading-6",
        type="circle",
        children=[dcc.Graph(id='plot-6-output', style={'height': '450px'})]
    ),

    html.Hr(),

    html.H3('검색된 건물 대비 연면적/노후도 유사 건물 평균 비교', style={'marginTop': '30px'}),
    dcc.Loading(
        id="loading-7",
        type="circle",
        children=[dcc.Graph(id='plot-7-output', style={'height': '450px'})]
    ),

])

# ==============================================================================
# 4. 콜백 정의
# ==============================================================================

# 🌟 클라이언트사이드 콜백으로 외부 클릭 감지
# ==============================================================================
# 🌟 모달 애니메이션 콜백 (기존 toggle_year_modal, toggle_gu_modal, toggle_dong_modal 대체)
# ==============================================================================

# 🌟 1. 년도 모달 - clientside callback으로 완전 변경
app.clientside_callback(
    """
    function(open_click, close_click, outside_click) {
        const modal = document.getElementById('year-modal-container');
        const box = document.getElementById('year-modal-box');

        if (!modal || !box) return window.dash_clientside.no_update;

        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered || ctx.triggered.length === 0) {
            return window.dash_clientside.no_update;
        }

        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];

        // 열기
        if (trigger_id === 'open-year-modal-btn') {
            modal.style.display = 'block';
            box.classList.remove('hide');
            modal.classList.remove('hide');
            return window.dash_clientside.no_update;
        }

        // 닫기 (버튼 또는 외부 클릭)
        if (trigger_id === 'close-year-modal-btn' || trigger_id === 'year-modal-open') {
            box.classList.add('hide');
            modal.classList.add('hide');

            // 애니메이션 끝나면 display: none
            setTimeout(() => {
                modal.style.display = 'none';
                box.classList.remove('hide');
                modal.classList.remove('hide');
            }, 200); // CSS animation duration과 맞춤

            return false; // Store 초기화
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output('year-modal-open', 'data', allow_duplicate=True),
    [Input('open-year-modal-btn', 'n_clicks'),
     Input('close-year-modal-btn', 'n_clicks'),
     Input('year-modal-open', 'data')],
    prevent_initial_call=True
)

# 🌟 2. 구 모달 - clientside callback으로 완전 변경
app.clientside_callback(
    """
    function(open_click, close_click, outside_click) {
        const modal = document.getElementById('gu-modal-container');
        const box = document.getElementById('gu-modal-box');

        if (!modal || !box) return window.dash_clientside.no_update;

        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered || ctx.triggered.length === 0) {
            return window.dash_clientside.no_update;
        }

        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];

        if (trigger_id === 'open-gu-modal-btn') {
            modal.style.display = 'block';
            box.classList.remove('hide');
            modal.classList.remove('hide');
            return window.dash_clientside.no_update;
        }

        if (trigger_id === 'close-gu-modal-btn' || trigger_id === 'gu-modal-open') {
            box.classList.add('hide');
            modal.classList.add('hide');

            setTimeout(() => {
                modal.style.display = 'none';
                box.classList.remove('hide');
                modal.classList.remove('hide');
            }, 200);

            return false;
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output('gu-modal-open', 'data', allow_duplicate=True),
    [Input('open-gu-modal-btn', 'n_clicks'),
     Input('close-gu-modal-btn', 'n_clicks'),
     Input('gu-modal-open', 'data')],
    prevent_initial_call=True
)

# 🌟 3. 동 모달 - clientside callback으로 완전 변경
app.clientside_callback(
    """
    function(open_click, close_click, outside_click) {
        const modal = document.getElementById('dong-modal-container');
        const box = document.getElementById('dong-modal-box');

        if (!modal || !box) return window.dash_clientside.no_update;

        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered || ctx.triggered.length === 0) {
            return window.dash_clientside.no_update;
        }

        const trigger_id = ctx.triggered[0].prop_id.split('.')[0];

        if (trigger_id === 'open-dong-modal-btn') {
            modal.style.display = 'block';
            box.classList.remove('hide');
            modal.classList.remove('hide');
            return window.dash_clientside.no_update;
        }

        if (trigger_id === 'close-dong-modal-btn' || trigger_id === 'dong-modal-open') {
            box.classList.add('hide');
            modal.classList.add('hide');

            setTimeout(() => {
                modal.style.display = 'none';
                box.classList.remove('hide');
                modal.classList.remove('hide');
            }, 200);

            return false;
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output('dong-modal-open', 'data', allow_duplicate=True),
    [Input('open-dong-modal-btn', 'n_clicks'),
     Input('close-dong-modal-btn', 'n_clicks'),
     Input('dong-modal-open', 'data')],
    prevent_initial_call=True
)


# ==============================================================================
# 기존 Python 콜백들은 모두 삭제하고 위의 clientside callback으로 교체
# 아래 콜백들을 삭제하세요:
# - toggle_year_modal
# - toggle_gu_modal
# - toggle_dong_modal
# ==============================================================================


# # 1. 년도 모달 열고 닫기
# @app.callback(
#     [Output("year-modal-container", "style"),
#      Output('year-modal-open', 'data', allow_duplicate=True)],
#     [Input("open-year-modal-btn", "n_clicks"),
#      Input("close-year-modal-btn", "n_clicks"),
#      Input('year-modal-open', 'data')],
#     prevent_initial_call=True
# )
# def toggle_year_modal(open_click, close_click, modal_open):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate
#
#     trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
#
#     if trigger_id == "open-year-modal-btn":
#         return {"display": "block"}, False
#     elif trigger_id == "close-year-modal-btn":
#         return {"display": "none"}, False
#     elif trigger_id == 'year-modal-open' and modal_open:
#         return {"display": "none"}, False
#
#     raise dash.exceptions.PreventUpdate


# 2. 년도 체크리스트 값을 Store에 저장
@app.callback(
    Output('selected-years-store', 'data'),
    Input('year-selection-checklist', 'value')
)
def store_selected_years(years):
    if not years:
        return ['전체 평균']
    return years


# 3. 1, 2번 그래프 업데이트
@app.callback(
    [Output('plot-1-output', 'figure'), Output('plot-2-output', 'figure')],
    [Input('house-type-1-2', 'value'), Input('energy-metric-1-2', 'value'),
     Input('selected-years-store', 'data'),
     Input('start-month-1-2', 'value'),
     Input('end-month-1-2', 'value'), Input('graph-type-1-2', 'value')]
)
def update_graph_1_2(house_type, energy_metric_name, year_selection_list, start_month, end_month, graph_type):
    return plot_interactive_gradio_1_2(house_type, energy_metric_name, year_selection_list, start_month, end_month,
                                       graph_type)


# # 4. 구 모달 열고 닫기
# @app.callback(
#     Output("gu-modal-container", "style"),
#     [Input("open-gu-modal-btn", "n_clicks"),
#      Input("close-gu-modal-btn", "n_clicks")],
#     prevent_initial_call=True
# )
# def toggle_gu_modal(open_click, close_click):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate
#     button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#     if button_id == "open-gu-modal-btn":
#         return {"display": "block"}  # 🌟 flex → block으로 변경
#     else:
#         return {"display": "none"}


# 5. 구 체크리스트 값을 Store에 저장
@app.callback(
    Output('selected-gu-store', 'data'),
    Input('gu-checklist-modal', 'value')
)
def store_selected_gu(gu_list):
    if not gu_list:
        return [initial_gu_name]
    return gu_list


# 6. 3번 그래프 (구별 비교) 업데이트
@app.callback(
    Output('plot-3-output', 'figure'),
    [Input('house-type-3', 'value'), Input('energy-metric-3', 'value'),
     Input('selected-gu-store', 'data'),
     Input('year-selection-3', 'value'), Input('start-month-3', 'value'),
     Input('end-month-3', 'value'), Input('graph-type-3', 'value')]
)
def update_graph_3(house_type, energy_metric_name, gu_selection_list, year_selection, start_month, end_month,
                   graph_type):
    if not gu_selection_list:
        gu_selection_list = [initial_gu_name]
    return plot_gu_comparison(house_type, energy_metric_name, gu_selection_list, year_selection, start_month, end_month,
                              graph_type)


# # 7. 동 모달 열고 닫기
# @app.callback(
#     Output("dong-modal-container", "style"),
#     [Input("open-dong-modal-btn", "n_clicks"),
#      Input("close-dong-modal-btn", "n_clicks")],
#     prevent_initial_call=True
# )
# def toggle_dong_modal(open_click, close_click):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate
#     button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#     if button_id == "open-dong-modal-btn":
#         return {"display": "block"}  # 🌟 flex → block으로 변경
#     else:
#         return {"display": "none"}


# 8. 동적 동 옵션 업데이트
@app.callback(
    Output('dong-checklist-3-1', 'options'),
    [Input('gu-dropdown-3-1', 'value')]
)
def set_dong_options_3_1(gu_name):
    if gu_name:
        dong_list = ['전체 동 평균'] + gu_to_dong_map.get(gu_name, [])
        return [{'label': i, 'value': i} for i in dong_list]
    return []


# 9. 동 체크리스트 값을 Store에 저장
@app.callback(
    Output('selected-dong-store', 'data'),
    Input('dong-checklist-3-1', 'value')
)
def store_selected_dong(dong_list):
    if not dong_list:
        return ['전체 동 평균']
    return dong_list


# 10. 3-1번 동별 비교 업데이트
@app.callback(
    Output('plot-3-1-output', 'figure'),
    [Input('house-type-3-1', 'value'), Input('energy-metric-3-1', 'value'),
     Input('gu-dropdown-3-1', 'value'),
     Input('selected-dong-store', 'data'),
     Input('year-selection-3-1', 'value'), Input('start-month-3-1', 'value'),
     Input('end-month-3-1', 'value'), Input('graph-type-3-1', 'value')]
)
def update_graph_3_1(house_type, energy_metric_name, gu_name, dong_selection_list, year_selection, start_month,
                     end_month,
                     graph_type):
    if not dong_selection_list:
        dong_selection_list = ['전체 동 평균']
    return plot_dong_comparison(house_type, energy_metric_name, gu_name, dong_selection_list, year_selection,
                                start_month,
                                end_month, graph_type)


# 11. 4, 5번 그래프 업데이트
@app.callback(
    [Output('plot-4-output', 'figure'), Output('plot-5-output', 'figure')],
    [Input('energy-metric-4-5', 'value'), Input('house-type-4-5', 'value')]
)
def update_graph_4_5(energy_metric_name, house_type):
    fig4 = plot_age_group_usage(energy_metric_name, house_type)
    fig5 = plot_age_group_per_grfa(energy_metric_name, house_type)
    return fig4, fig5


# 12. 6번 그래프 업데이트
@app.callback(
    Output('plot-6-output', 'figure'),
    [Input('target-match-key', 'value'), Input('energy-metric-6-7', 'value')]
)
def update_graph_6(target_match_key, energy_metric_name):
    return plot_neighborhood_comparison(target_match_key, energy_metric_name)


# 13. 7번 그래프 업데이트
@app.callback(
    Output('plot-7-output', 'figure'),
    [Input('target-match-key', 'value'), Input('energy-metric-6-7', 'value')]
)
def update_graph_7(target_match_key, energy_metric_name):
    return plot_similarity_comparison(target_match_key, energy_metric_name)


# 14. 주소 검색 API 콜백
@app.callback(
    [Output('target-match-key', 'value'), Output('search-status-output', 'children')],
    [Input('search-button', 'n_clicks')],
    [dash.dependencies.State('search-address-input', 'value')]
)
def handle_address_search(n_clicks, search_query):
    if n_clicks is None or n_clicks == 0 or not search_query:
        return dash.no_update, ""

    target_lat, target_lon, full_address, search_type = search_query_kakao(search_query)

    if target_lat is None:
        return dash.no_update, f"❌ 검색 실패: {full_address}"

    df_temp = df_data.drop_duplicates(subset=[JOIN_KEY]).copy()

    def calculate_distance(row):
        if pd.isna(row['LATITUDE']) or pd.isna(row['LONGITUDE']): return np.inf
        if abs(row['LATITUDE']) > 90 or abs(row['LONGITUDE']) > 180: return np.inf

        target_coords = (target_lat, target_lon)
        building_coords = (row['LATITUDE'], row['LONGITUDE'])
        return geodesic(target_coords, building_coords).m

    df_temp['DISTANCE_M'] = df_temp.apply(calculate_distance, axis=1)

    df_valid_dist = df_temp[df_temp['DISTANCE_M'] != np.inf]

    if not df_valid_dist.empty:
        closest_building = df_valid_dist.loc[df_valid_dist['DISTANCE_M'].idxmin()]
        closest_match_key = closest_building[JOIN_KEY]
        closest_distance = closest_building['DISTANCE_M']

        status_text = (
            f"✅ 카카오 {search_type.replace(' 성공', '')}: '{full_address}'. "
            f"가장 가까운 데이터 건물: **'{closest_match_key}'** (거리: {closest_distance:.2f}m) 로 지정됩니다."
        )
        return closest_match_key, status_text
    else:
        status_text = f"⚠️ '{full_address}' 주변에 비교할 건물 데이터가 없거나 유효한 위/경도 정보가 부족합니다."
        return dash.no_update, status_text


# ==============================================================================
# 5. 앱 실행
# ==============================================================================


if __name__ == '__main__':
    print("=" * 80)
    print("### 📊 Dash 웹 앱 실행 중... ")
    print("=" * 80)

    app.run(host='0.0.0.0', debug=True, dev_tools_ui=False)

