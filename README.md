# 🏙️ Daejeon Energy Insight (E-PRO)

> **"Data-Driven Digital Twin Platform for Urban Energy Efficiency"**  
> 대전광역시 3D 건물 에너지 통합 분석 및 AI 소비 예측 시뮬레이터

![Project Banner](https://via.placeholder.com/1200x500.png?text=Daejeon+Energy+Insight+Dashboard)
*(Update this image linking to your project screenshot)*

## 📝 Project Overview (프로젝트 개요)

**Daejeon Energy Insight**는 대전광역시의 건물 에너지(전기/가스) 사용량을 **3D 지도(V-World)** 기반으로 시각화하고, **AI(Prophet)**를 활용해 미래 에너지 수요를 예측하는 통합 관리 플랫폼입니다.
단순한 통계 조회를 넘어, 개별 건물의 에너지 효율을 진단하고 이웃 건물과 비교(Benchmarking)함으로써 **'노후 그레이존'의 에너지 낭비 문제**를 데이터로 입증하고 개선 방향을 제시합니다.

---

## 🚀 Key Features (핵심 기능)

### 1. 3D Building Visualization (디지털 트윈)
- **V-World WebGL API**를 활용하여 대전시 전역의 건물을 3D로 시각화했습니다.
- **노후도 매핑(Age Coloring)**: 건축물 대장 데이터와 매핑하여, 건물의 연식에 따라 `신축(0~9년)`부터 `노후(30년+)`까지 **Red-Scale Gradient**로 건물 색상을 동적으로 표현합니다.

### 2. AI Energy Forecaster (12개월 예측 시뮬레이터)
- **Facebook Prophet** 알고리즘을 적용하여 향후 1년의 에너지 소비 패턴을 예측합니다.
- **Seasonality Handling**: 겨울철 난방, 여름철 냉방 등 계절적 패턴을 정교하게 학습하여 단순 추세선이 아닌 실제와 가까운 예측 굴곡을 제공합니다.
- **Interactive Simulator**: 사용자가 `노후도`, `건물유형` 등의 변수를 조절하면 실시간으로 예측 그래프가 업데이트됩니다.

### 3. Macro Trend Analysis (거시적 트렌드 분석)
- **다차원 필터링**: 주택 유형, 에너지원, 기간을 자유롭게 조합하여 데이터를 추출합니다.
- **이중 관점 비교**: 
    - **절대 사용량(Total)**: "전기를 가장 많이 쓰는 달은 언제인가?"
    - **면적당 효율(Efficiency)**: "면적($1m^2$)당 얼마나 쓰는가?" (건물 크기 변수를 제거하여 순수 효율성 비교)

### 4. Smart Benchmarking (정밀 비교 진단)
- 특정 건물을 선택하면 두 가지 기준으로 에너지 효율 순위를 매깁니다.
    - **위치 기반(Proximity)**: 반경 100m 이내 이웃 건물들과 비교 (기후/상권 변수 통제)
    - **구조 기반(Structure)**: 연면적/노후도가 유사한 '쌍둥이 스펙' 건물들과 비교 (구조적 효율성 진단)

---

## 🛠️ Tech Stack (사용 기술)

| **Class** | **Technology** | **Usage (용도)** |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JS, Thymeleaf, Chart.js | UI 구현 및 2D 에너지 그래프 시각화 |
| **Backend** | Java (Spring Boot), Python (Flask) | 메인 웹 서버 및 AI 모델 서빙(Serving) |
| **Data & AI** | Python (Pandas), Dash, Prophet | 데이터 전처리, 대시보드 구축, 수요 예측 |
| **Database** | Oracle DB | 건물 대장 및 월별 에너지 데이터 저장 |
| **API** | V-World API, Kakao Local API | 3D 지도 렌더링, 주소 검색 및 좌표 변환 |

---

## ⚙️ Engineering Challenges & Solutions

### 1. 대용량 공공 데이터 전처리 (Data Processing)
- **Issue**: 수 GB의 CSV 데이터를 엑셀로 열 수 없고, 메모리 초과(OOM) 오류 발생.
- **Solution**: **Streaming Parsing (OpenCSV)** 방식을 도입해 Row 단위로 처리하여 메모리를 최적화했습니다. 분절된 전기/가스 데이터를 `Java Map`을 활용해 단일 객체로 병합(Merge)하고, 결측치를 전처리 단계에서 필터링했습니다.

### 2. 외부 API CORS 이슈 해결
- **Issue**: 브라우저에서 V-World API 호출 시 `Cross-Origin` 차단 발생.
- **Solution**: Spring Boot 내에 **Proxy Server (`/api/get_address`)**를 구축하여 Server-to-Server 통신으로 데이터를 중계, 보안 정책을 우회하였습니다.

### 3. 이기종 데이터 좌표 매칭 (Geo-Spatial Query)
- **Issue**: 에너지 데이터의 주소와 지도 API의 좌표가 미세하게 불일치하여 매핑 실패.
- **Solution**: 단순 문자열 일치가 아닌, **Bounding Box (반경 검색) & Nearest Neighbor** 알고리즘을 적용하여 매칭 정확도를 99% 수준으로 끌어올렸습니다.

### 4. Oracle-MyBatis 매핑 이슈
- **Issue**: DB 컬럼(UPPER_CASE)과 Java 객체(camelCase) 간 매핑 실패로 `null` 반환.
- **Solution**: MyBatis 설정(`map-underscore-to-camel-case: true`)을 적용하여 자동 변환을 활성화했습니다.

---

## 📂 Repository Structure

```
Daejeon_Energy_Insight/
├── src/main/java/       # Spring Boot Backend Code
├── src/main/resources/  # Templates (Thymeleaf), Static Assets
├── python_scripts/      # Flask Server & AI Models (Prophet)
└── README.md            # Project Documentation
```

---

## 👨‍💻 Author

*   **Developer**: MinSung (Project Lead, Full-Stack)
*   **Role**: 3D Map Implementation, AI Modeling Integration, Data Pipeline Construction
