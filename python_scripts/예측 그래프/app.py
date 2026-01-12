# -*- coding: utf-8 -*-
# app.py
import os
import pandas as pd
import geopandas as gpd
import sys
from flask import Flask, request, jsonify, render_template, abort
import requests
print("--- [EPRO] Flask 서버: 1단계 CSV 로드 및 GDF 변환 시작 ---")
DF_BUILD_GDF = None
DF_BUILD_GDF_METER = None
try:
    # 1. CSV 로드 (파일명/경로 필요 시 수정)
    df_bulid = pd.read_csv("daejeon_filtered_buildings.csv", encoding='utf-8-sig')

    # 2. GeoDataFrame으로 변환 (CRS: EPSG:4326, 위도/경도)
    DF_BUILD_GDF = gpd.GeoDataFrame(
        df_bulid,
        geometry=gpd.points_from_xy(df_bulid.경도, df_bulid.위도),
        crs="EPSG:4326"
    )

    # 3. 빠른 탐색을 위해 '미터' 단위 좌표계로 변환 (EPSG:3857)
    DF_BUILD_GDF_METER = DF_BUILD_GDF.to_crs(epsg=3857)

    print(f"--- 1단계 GDF (EPSG:3857) 메모리 로드 성공: {len(DF_BUILD_GDF_METER)} 건 ---")

except FileNotFoundError:
    print("!!! 치명적 오류: 'daejeon_filtered_buildings.csv' 파일을 찾을 수 없습니다.")
    sys.exit()
except KeyError as e:
    print(f"!!! 치명적 오류: {e} 컬럼이 CSV에 없습니다. ('위도' 또는 '경도')")
    sys.exit()
except Exception as e:
    print(f"GDF 생성 실패: {e}")
    sys.exit()
# --- [EPRO 1. 완료] ---

# VWorld 키 (환경변수 우선)
VWORLD_KEY = os.getenv("3907B382-CD3D-304B-A82F-C7BFA4286232", "3907B382-CD3D-304B-A82F-C7BFA4286232")

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


# 3-1. 메인 페이지
@app.route('/')
def index():
    return render_template('Epro_dashboard.html', vworld_key=VWORLD_KEY)


# 3-2. 좌표 → 도로명 주소 (리버스 지오코딩, 프록시)
@app.route('/api/get_address')
def get_address():
    lon = request.args.get('lon')
    lat = request.args.get('lat')

    if not lon or not lat:
        return jsonify({"error": "lon/lat missing"}), 400

    api_url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getaddress",
        "crs": "epsg:4326",
        "point": f"{lon},{lat}",
        "format": "json",
        "type": "road",
        "key": VWORLD_KEY
    }

    try:
        response = requests.get(api_url, params=params, timeout=7)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3-3. 주소 → 좌표 (지오코딩, 프록시)
@app.route('/api/geocode')
def geocode():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "query missing"}), 400

    base_url = "https://api.vworld.kr/req/address"
    common_params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": query,
        "refine": "true",
        "simple": "false",
        "format": "json",
        "key": VWORLD_KEY
    }

    try:
        # 1차: 도로명
        params_road = {**common_params, "type": "road"}
        r = requests.get(base_url, params=params_road, timeout=7)
        data = r.json()

        # 도로명 실패하면 지번으로 2차 시도
        if (
            "response" not in data
            or data["response"]["status"] != "OK"
            or len(data["response"]["result"]) == 0
        ):
            params_parcel = {**common_params, "type": "parcel"}
            r = requests.get(base_url, params=params_parcel, timeout=7)
            data = r.json()

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/search_address')
def search_address():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "keyword missing"}), 400

    params = {
        "service": "search",
        "request": "search",
        "version": "2.0",
        "crs": request.args.get('crs', 'EPSG:4326'),
        "size": request.args.get('size', '10'),
        "page": request.args.get('page', '1'),
        "query": keyword,
        "type": request.args.get('type', 'address'),
        "format": "json",
        "errorformat": "json",
        "key": VWORLD_KEY,
    }

    data_param = request.args.get('data')
    if (data_param):
        params["data"] = data_param
    elif params["type"] == 'address':
        params["data"] = 'LT_C_AISBR'

    category_param = request.args.get('category')
    if category_param:
        params["category"] = category_param

    domain_param = request.args.get('domain')
    if domain_param:
        params["domain"] = domain_param

    try:
        response = requests.get('https://api.vworld.kr/req/search', params=params, timeout=7)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3-4. 좌표로 EPRO CSV에서 가장 가까운 건물 찾기
@app.route("/api/get-data-from-coords", methods=['GET'])
def get_data_from_coords():
    global DF_BUILD_GDF_METER
    global DF_BUILD_GDF

    lon_str = request.args.get('lon')
    lat_str = request.args.get('lat')
    if not lon_str or not lat_str:
        abort(400, description="lon 또는 lat 파라미터가 누락되었습니다.")

    try:
        lon = float(lon_str)
        lat = float(lat_str)
    except ValueError:
        abort(400, description="lon/lat이 숫자가 아닙니다.")

    click_point = gpd.GeoDataFrame(
        [{'geometry': gpd.points_from_xy([lon], [lat])[0]}],
        crs="EPSG:4326"
    )
    click_point_meter = click_point.to_crs(DF_BUILD_GDF_METER.crs)

    nearest_join = gpd.sjoin_nearest(
        click_point_meter,
        DF_BUILD_GDF_METER,
        how='inner',
        max_distance=20
    )

    if nearest_join.empty:
        print(f"[Flask 프록시] 매칭 실패. (20m 반경 내 건물 없음)")
        abort(404, description="20m 반경 내 Epro 데이터를 찾지 못했습니다.")

    nearest_index = nearest_join.iloc[0]['index_right']
    found_data_series = DF_BUILD_GDF.loc[nearest_index]

    distance = click_point_meter.geometry.distance(
        DF_BUILD_GDF_METER.loc[nearest_index].geometry
    ).iloc[0]

    found_data = found_data_series.to_dict()
    if 'geometry' in found_data:
        del found_data['geometry']

    print(f"[Flask 프록시] {distance:.1f}m 거리에서 매칭 성공!")
    return jsonify({
        "status": "OK",
        "distance_m": round(distance, 2),
        "data": found_data
    })

import matplotlib
matplotlib.use("Agg")  # 서버용 백엔드
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
import pickle
import io
import base64

import platform

# 한글 폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
else:
    # Linux/Mac 등 (NanumGothic이 설치되어 있어야 함)
    plt.rc('font', family='NanumGothic')

matplotlib.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------------------
# 2. pkl 로드 (df: 실제, future_df: 예측)
#    ex_sqlld3.py 에서 생성한 energy_data.pkl 사용
# ------------------------------------------------------------
with open("energy_data.pkl", "rb") as f:
    data = pickle.load(f)

df = data["df"]
future_df = data["future_df"]

# 선택 리스트
HOUSE_TYPES = ["단독주택", "공동주택"]
AGE_GROUPS = ["A_0~9년", "B_10~19년", "C_20~29년", "D_30년 이상"]

METRIC_LABELS = {
    "USE_GAS": "가스 사용량",
    "USE_ELECTRIC": "전기 사용량",
    "TOE_GAS": "가스 TOE",
    "TOE_ELECTRIC": "전기 TOE",
    "CARBON_GAS": "가스 탄소배출량",
    "CARBON_ELECTRIC": "전기 탄소배출량",
}

CHART_TYPES = ["line", "bar", "area", "radar"]  # radar는 일부에서 line으로 대체


# ------------------------------------------------------------
# 3. 시간축 그래프 (실제 + 예측) 생성 함수
# ------------------------------------------------------------
def make_plot(house, age, metric, chart_type="line"):
    pred_col = f"{metric}_PRED"

    # 1) 실제 데이터
    hist = df[(df["HOUSE_TYPE"] == house) & (df["AGE_GROUP"] == age)]
    if hist.empty:
        return None

    hist_grp = (
        hist.groupby("DATE")[metric]
        .mean()
        .reset_index()
        .sort_values("DATE")
        .rename(columns={metric: "VALUE"})
    )

    # 2) 예측 데이터
    fut = future_df[
        (future_df["HOUSE_TYPE"] == house)
        & (future_df["AGE_GROUP"] == age)
    ][["DATE", pred_col]].copy()

    if fut.empty:
        return None

    fut = (
        fut.sort_values("DATE")
        .rename(columns={pred_col: "VALUE"})
    )

    # 3) 연속 보정 (첫 예측값을 마지막 실제값에 맞추기)
    last_actual = hist_grp["VALUE"].iloc[-1]
    first_pred = fut["VALUE"].iloc[0]
    shift = last_actual - first_pred
    fut["VALUE"] = fut["VALUE"] + shift

    # 🔗 실제 마지막 점 + 예측 구간을 이어서 사용할 데이터
    pred_dates = pd.concat([hist_grp["DATE"].tail(1), fut["DATE"]])
    pred_vals = pd.concat([hist_grp["VALUE"].tail(1), fut["VALUE"]])

    # radar는 시간축에 안 맞으니까 line으로 강제 변환
    if chart_type == "radar":
        chart_type = "line"

    fig, ax = plt.subplots(figsize=(8, 3))

    # -----------------------------
    #   실제 데이터
    # -----------------------------
    if chart_type == "line":
        ax.plot(hist_grp["DATE"], hist_grp["VALUE"], "-", label="실제")

    elif chart_type == "bar":
        ax.bar(hist_grp["DATE"], hist_grp["VALUE"], label="실제", alpha=0.7)

    elif chart_type == "area":
        ax.fill_between(hist_grp["DATE"], hist_grp["VALUE"], alpha=0.4, label="실제")

    # -----------------------------
    #   예측 데이터 (실제 마지막 점에서부터 이어서)
    # -----------------------------
    if chart_type == "line":
        ax.plot(pred_dates, pred_vals, "--", label="예측(보정)")

    elif chart_type == "bar":
        ax.bar(fut["DATE"], fut["VALUE"], label="예측(보정)", alpha=0.5)

    elif chart_type == "area":
        ax.fill_between(pred_dates, pred_vals, alpha=0.3, label="예측(보정)")

    ax.set_title(f"{house} / {age} – {METRIC_LABELS[metric]}")
    ax.legend()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)

    return img_base64


# ------------------------------------------------------------
# 4. 노후도 그룹별 예측값 비교 그래프 생성
# ------------------------------------------------------------
def make_compare_plot(house, metric, chart_type="bar"):
    pred_col = f"{metric}_PRED"

    sub = future_df[future_df["HOUSE_TYPE"] == house]
    if sub.empty:
        return None

    grp = (
        sub.groupby("AGE_GROUP")[pred_col]
        .mean()
        .reset_index()
        .rename(columns={pred_col: "VALUE"})
    )

    # 노후도 순서 정렬
    grp["AGE_GROUP"] = pd.Categorical(grp["AGE_GROUP"], categories=AGE_GROUPS, ordered=True)
    grp = grp.sort_values("AGE_GROUP")
    grp = grp[grp["AGE_GROUP"].notna()]

    if grp.empty:
        return None

    labels = grp["AGE_GROUP"].tolist()
    values = grp["VALUE"].tolist()
    n = len(labels)

    if chart_type == "radar":
        # 레이더 차트
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))
        vals = np.concatenate((values, [values[0]]))

        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={"projection": "polar"})
        ax.plot(angles, vals, marker="o")
        ax.fill(angles, vals, alpha=0.25)
        ax.set_xticks(np.linspace(0, 2 * np.pi, n, endpoint=False))
        ax.set_xticklabels(labels)
        ax.set_title(f"{house} – {METRIC_LABELS[metric]} (노후도별 예측 비교)")
    else:
        fig, ax = plt.subplots(figsize=(8, 3))
        x = np.arange(n)

        if chart_type == "line":
            ax.plot(x, values, marker="o")
        elif chart_type == "bar":
            ax.bar(x, values)
        elif chart_type == "area":
            ax.fill_between(x, values, alpha=0.4)
            ax.plot(x, values, marker="o")

        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel(METRIC_LABELS[metric])
        ax.set_title(f"{house} – {METRIC_LABELS[metric]} (노후도별 예측 비교)")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(fig)

    return img_base64


# ------------------------------------------------------------
# 5. 절감 시뮬레이터용 기준 시계열 추출
# ------------------------------------------------------------
def get_baseline_series(house, age, metric):
    """
    선택된 조건에 대해
    - hist_dates, hist_values : 실제 구간
    - fut_dates, fut_values   : 보정된 예측 구간
    반환
    """
    pred_col = f"{metric}_PRED"

    hist = df[(df["HOUSE_TYPE"] == house) & (df["AGE_GROUP"] == age)]
    if hist.empty:
        return None

    hist_grp = (
        hist.groupby("DATE")[metric]
        .mean()
        .reset_index()
        .sort_values("DATE")
        .rename(columns={metric: "VALUE"})
    )

    fut = future_df[
        (future_df["HOUSE_TYPE"] == house)
        & (future_df["AGE_GROUP"] == age)
    ][["DATE", pred_col]].copy()

    if fut.empty:
        return None

    fut = (
        fut.sort_values("DATE")
        .rename(columns={pred_col: "VALUE"})
    )

    # 연속 보정
    last_actual = hist_grp["VALUE"].iloc[-1]
    first_pred = fut["VALUE"].iloc[0]
    shift = last_actual - first_pred
    fut["VALUE"] = fut["VALUE"] + shift

    hist_dates = hist_grp["DATE"].dt.strftime("%Y-%m-%d").tolist()
    hist_values = hist_grp["VALUE"].tolist()
    fut_dates = fut["DATE"].dt.strftime("%Y-%m-%d").tolist()
    fut_values = fut["VALUE"].tolist()

    return {
        "hist_dates": hist_dates,
        "hist_values": hist_values,
        "fut_dates": fut_dates,
        "fut_values": fut_values,
    }

# ------------------------------------------------------------
# 6. 라우팅
# ------------------------------------------------------------
@app.route("/epro", methods=["GET", "POST"])
def epro():
    #  기본값: 리스트 첫 번째 애들
    default_house = HOUSE_TYPES[1]          # 예: "공동주택"
    default_age = AGE_GROUPS[2]             # 예: "C_20~29년"
    default_metric = list(METRIC_LABELS.keys())[0]   # 딕셔너리 첫 키
    default_chart = "line"

    if request.method == "POST":
        house_type = request.form.get("house_type", default_house)
        age_group = request.form.get("age_group", default_age)
        metric = request.form.get("metric", default_metric)
        chart_type = request.form.get("chart_type", default_chart)
    else:
        # 처음 들어와도 그래프가 바로 보이도록 기본값 사용
        house_type = request.args.get("house_type", default_house)
        age_group = request.args.get("age_group", default_age)
        metric = request.args.get("metric", default_metric)
        chart_type = request.args.get("chart_type", default_chart)

    #  PNG 그래프 (line, area 에서 사용 / bar일 때도 백업용으로 그대로 생성)
    plot_data = make_plot(house_type, age_group, metric, chart_type)


    return render_template(
        "result.html",
        house_types=HOUSE_TYPES,
        age_groups=AGE_GROUPS,
        metric_labels=METRIC_LABELS,
        chart_types=CHART_TYPES,
        selected_house=house_type,
        selected_age=age_group,
        selected_metric=metric,
        selected_chart_type=chart_type,
        plot_data=plot_data,
    )




@app.route("/compare", methods=["GET", "POST"])
def compare():
    #  기본값: 리스트 첫 번째 애들
    default_house = HOUSE_TYPES[0]                 # 예: "단독주택"
    default_metric = list(METRIC_LABELS.keys())[0] # METRIC_LABELS의 첫 번째 키
    default_chart = "line"

    if request.method == "POST":
        house_type = request.form.get("house_type", default_house)
        metric = request.form.get("metric", default_metric)
        chart_type = request.form.get("chart_type", default_chart)
    else:
        # 처음 들어와도 그래프를 바로 보이게 기본값 사용
        house_type = request.args.get("house_type", default_house)
        metric = request.args.get("metric", default_metric)
        chart_type = request.args.get("chart_type", default_chart)

    #  GET/POST 상관 없이 항상 그래프 생성
    plot_data = make_compare_plot(house_type, metric, chart_type)

    return render_template(
        "compare_result.html",
        house_types=HOUSE_TYPES,
        metric_labels=METRIC_LABELS,
        chart_types=CHART_TYPES,
        selected_house=house_type,
        selected_metric=metric,
        selected_chart_type=chart_type,
        plot_data=plot_data,
    )


@app.route("/simulator", methods=["GET"])
def simulator():
    house_type = request.args.get("house_type", "공동주택")
    age_group = request.args.get("age_group", "A_0~9년")
    metric = request.args.get("metric", "USE_ELECTRIC")

    series = get_baseline_series(house_type, age_group, metric)

    return render_template(
        "simulator.html",
        house_types=HOUSE_TYPES,
        age_groups=AGE_GROUPS,
        metric_labels=METRIC_LABELS,
        selected_house=house_type,
        selected_age=age_group,
        selected_metric=metric,
        series=series,
    )



# 이렇게 변경하세요
if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8051, debug=True,threaded=True)
    app.run(host='0.0.0.0', port=8051, threaded=True)
