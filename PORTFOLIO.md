# 🏗️ 대전 그린 에너지 빌딩 플랫폼 (E-PRO)

## 1. 프로젝트 개요 (Project Overview)
> **핵심 컨셉**: 대전시 공공 데이터 기반의 건물 에너지 효율 관리 및 모니터링 GIS 플랫폼.
**E-PRO** 시스템은 공공 건물 데이터를 리얼타임 지도 시각화와 결합하여, 에너지 사용량 및 상세 건축물 정보를 직관적으로 제공합니다.

- **유형**: 공공 데이터 활용 / 공간 정보(GIS) 웹 애플리케이션
- **역할**: Full Stack Developer (기여도: 100%)
- **상태**: 개발 단계 (로직 고도화 및 UI 개선 중)

---

## 1.5 시스템 아키텍처 (System Architecture)

```mermaid
graph LR
    User((User)) -->|접속| Client[Web Browser<br/>(Thymeleaf / JS / HTML / CSS)]
    
    subgraph Frontend [Frontend Layer]
        Client -->|지도 API| VWorld[V-World API]
    end

    Client -->|HTTP 요청| Server[Spring Boot Server<br/>(Java 17)]
    
    subgraph Backend [Backend Layer]
        Server -->|데이터 파싱| CSVParser[OpenCSV Library]
        Server -->|ORM 매핑| Mapper[MyBatis Framework]
    end
    
    subgraph Data [Data Layer]
        CSV[공공 데이터 CSV] -->|File Read| CSVParser
        Mapper <-->|JDBC| DB[(Oracle Database)]
    end
    
    %% Green Color Theme
    style User fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style Client fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style VWorld fill:#a5d6a7,stroke:#1b5e20,stroke-width:2px
    style Server fill:#81c784,stroke:#1b5e20,stroke-width:2px
    style CSVParser fill:#66bb6a,stroke:#1b5e20,color:white
    style Mapper fill:#66bb6a,stroke:#1b5e20,color:white
    style DB fill:#43a047,stroke:#1b5e20,color:white
    style CSV fill:#4caf50,stroke:#1b5e20,color:white
```

---

## 2. 기술 스택 (Technology Stack)

### 🛠️ Tech Stack Summary

| 분류 (Category) | 기술 (Technology) | 상세 내용 (Details) |
| :--- | :--- | :--- |
| **Backend** | **Spring Boot** | 3.5.7 (Java 17) |
| | **MyBatis** | 3.0.5 (Oracle 11g/19c 연동) |
| | **OpenCSV** | 대용량 건축물 대장 파싱 |
| **Frontend** | **Thymeleaf** | SSR Template Engine |
| | **JavaScript** | ES6+, jQuery (DOM/Ajax) |
| | **Chart.js** | 데이터 시각화 (에너지 그래프) |
| **Data / AI** | **Python** | Pandas, NumPy, Scikit-learn |
| | **GeoPandas** | 공간 데이터 분석 (EPSG 변환) |
| | **Plotly Dash** | 데이터 분석 대시보드 |
| **Infra / Tool** | **Oracle DB** | 관계형 데이터베이스 |
| | **Maven** | 의존성 관리 |

### 🌐 Key APIs & External Services

| 서비스명 (Service) | API 유형 (Type) | 활용 목적 (Usage) |
| :--- | :--- | :--- |
| **V-World** | **WebGL Map 3.0** | 메인 3D 지도 시각화 (건물/지형 렌더링) |
| (공간정보오픈플랫폼) | **Geocoder 2.0** | 좌표(WGS84) ↔ 주소(도로명/지번) 변환 |
| | **Search 2.0** | 주소 기반 건축물 대장 상세 정보 조회 |
| **Kakao Map** | **Local API** | 주소 검색 보정 및 키워드 검색 (데이터 전처리용) |
| **공공데이터포털** | **File Data** | 건축물 대장 표제부 (CSV) 데이터 원천 |

---

## 3. 주요 기능 (Key Features)

### 🗺️ 인터랙티브 GIS 지도 서비스 & V-World API 활용
- **V-World WebGL 3.0 기반 3D 지도**: 국가 공간정보 브이월드의 최신 **WebGL 3.0 API**를 도입하여 별도의 플러그인 설치 없이 웹 브라우저상에서 건물과 지형을 **고품질 3D**로 시각화했습니다.
- **건물 노후도 시각화 (Age-Based Color Coding)**: 
    - 건축물 대장의 **사용승인일** 데이터를 활용하여, 건물의 나이(노후도)에 따라 지도 및 마커의 색상을 다르게 표현하는 **동적 스타일링**을 적용했습니다.
    - 이를 통해 도시 내 노후 건물 밀집 지역이나 신축 구역을 직관적으로 파악할 수 모니터링 기능을 제공합니다.
- **지능형 클릭 이벤트 프로세스 (API 워크플로우)**:
    1. **Coordinate Capture**: WebGL 지도 상에서 건물 클릭 시 `ScreenSpaceEventHandler`를 통해 3차원 좌표를 획득하고, 이를 정밀한 위/경도 좌표로 변환합니다.
    2. **Geocoder API 2.0**: 획득한 좌표를 **V-World Geocoder API 2.0**으로 전송하여 해당 위치의 정확한 **도로명/지번 주소**로 변환(Reverse Geocoding)합니다.
    3. **Search API 2.0**: 변환된 주소를 키로 **Search API 2.0**을 호출하여 건물명, 용도, 층수 등 상세 건축물 대장 정보를 실시간으로 조회합니다.
- **에너지 정보 시각화 (Energy Graph)**:
    - 건물 선택 시, 해당 건물의 **전기, 가스, 총 에너지 사용량** 데이터를 DB에서 조회하여 **Chart.js** 기반의 Line/Bar 그래프로 사이드바에 즉시 표출합니다.
- **편의 기능 및 성능 최적화**:
    - **Mark Layer & Search**: 주소 및 건물명 검색 기능을 제공하고, 검색 결과 위치로 카메라가 부드럽게 이동(FlyTo)하며 마커 레이어 팝업을 띄웁니다.
    - **Bounding Box 최적화**: 현재 보고 있는 지도 영역(`minLat/maxLat`) 내의 건물만 DB에서 로딩하여 대용량 데이터 처리 성능을 극대화했습니다.
    > *Code Reference: `BuildingMasterMapper.findCandidatesByBoundingBox`, `script.js` (API Orchestration)*

### 📊 에너지 대시보드 및 분석
- **데이터 시각화**: 그래프(`Epro_graph.html`)를 통해 건물의 에너지 소비 추이와 통계를 시각적으로 제공합니다.
- **통합 대시보드**: 건물 용도, 연면적(`GRFA`), 층수 등 핵심 지표를 한눈에 볼 수 있는 대시보드(`Epro_dashboard.html`)를 구축했습니다.

### 🏢 상세 건축물 정보 조회
- **Deep Dive**: 상세 페이지(`Epro_detail.html`) 모달을 통해 다음과 같은 심층 정보를 제공합니다:
    - 데이터 기준일 (`DATA_STNDT`)
    - 주 구조 (`STRCT_CD`)
    - 사용 승인일 (`USE_APRV_Y`)
    - 지번 및 법정동 정보 (`LNNO`, `LEGALDONG`)

### 📢 소통 및 알림 공간
- **게시판 시스템**: 공지사항(`Epro_notice.html`)을 통해 시스템 업데이트 및 사용자 안내를 제공합니다.
- **통합 검색**: 지역(동) 및 건물명 기반 검색 기능을 지원합니다.

---

## 4. 데이터베이스 설계 (Core Table)

### `BUILDING_MASTER`
수만 건 이상의 대용량 건축물 데이터를 저장하는 핵심 테이블입니다.
| 컬럼명 (Column) | 타입 | 설명 |
| :--- | :--- | :--- |
| `BILD_ID` | PK | 건물 고유 식별자 |
| `LATITUDE` | DECIMAL | 위도 (GPS) |
| `LONGITUDE` | DECIMAL | 경도 (GPS) |
| `LEGALDONG` | VARCHAR | 법정동 명칭 |
| `GU_NAME` | VARCHAR | 자치구 명칭 |
| `GRFA` | NUMBER | 연면적 (Gross Floor Area) |

*(Derived from MyBatis Mappers)*

---

## 5. 트러블슈팅 및 챌린지 (Troubleshooting & Challenges)

### 🚀 Challenge 1: 대용량 공간 데이터 검색 속도 이슈
**문제(Problem)**: `BUILDING_MASTER` 테이블의 데이터가 방대하여, 지도 클릭 시 자바단에서 모든 건물의 거리를 계산하면 속도가 매우 느려지는 현상 발생.
**해결(Solution)**:
- 거리 계산 로직을 **Database Layer (SQL)**로 위임했습니다.
- **Bounding Box (사각형 범위)** 필터(`WHERE lat BETWEEN ... AND long BETWEEN ...`)를 먼저 적용하여 계산 후보군을 대폭 줄였습니다.
- 정렬 시 값비싼 제곱근(SQRT) 연산 대신 **거리의 제곱(Squared Euclidean Distance)** 공식을 사용하여 DB 부하를 최소화했습니다:
  ```sql
  ((LATITUDE - targetLat)^2 + (LONGITUDE - targetLon)^2) AS DISTANCE_SQ
  ```
- **결과**: 쿼리 응답 속도가 획기적으로 개선되어 끊김 없는 지도 인터랙션이 가능해졌습니다.

### 🌐 Challenge 2: 공공 데이터(CSV) 정합성 처리
**문제(Problem)**: 제공받은 CSV 공공 데이터에 결측치나 잘못된 포맷의 행(Row)이 존재하여 임포트 시 오류 발생.
**해결(Solution)**:
- **OpenCSV** 라이브러리를 도입하여 파싱 안정성을 확보했습니다.
- DB 적재 전 `daejeon.csv.path` 경로의 파일을 읽어 유효성을 검증하는 전처리 단계를 추가했습니다.
- Spring Boot의 트랜잭션 관리를 통해 대량 데이터 삽입 시 원자성(Atomicity)을 보장했습니다.

---

## 6. AI & Data Analytics (Python Module)
파이썬 기반의 별도 분석 모듈(`python_scripts`)을 통해 데이터 심층 분석 및 예측 기능을 수행합니다.

### 🧠 예측 모델링 (Time-Series Forecasting)
> *Reference Code: `예측 그래프/app.py`*
- **목표**: 건물 노후도 및 유형에 따른 미래 에너지 사용량(전기/가스) 및 탄소 배출량 예측.
- **구현 방식**:
    - **Data**: 과거 에너지 사용량 시계열 데이터 학습.
    - **Optimization**: 예측 데이터(`future_df`)와 실측 데이터(`hist`)의 연결 부위를 부드럽게 보정(Shift Correction)하여 시각적 연속성 확보.
    - **Serving**: Flask 서버를 통해 예측 결과를 JSON/Image 형태로 렌더링하여 웹 대시보드에 제공.

### 📍 고급 공간 분석 (Geospatial Analysis)
> *Reference Code: `GRAPH_KAKAO.py`, `app.py`*
- **GeoPandas & Shapely**:
    - 위/경도 좌표계(EPSG:4326)를 미터 좌표계(EPSG:3857)로 변환하여 정확한 거리 계산 수행.
    - `sjoin_nearest` 알고리즘을 사용하여 사용자 클릭 지점에서 **반경 20m 이내** 가장 가까운 건물을 0.1초 내로 매칭.
- **Data Enrichment**:
    - **Kakao / V-World API**: 건물 주소 및 키워드 검색 결과를 1/2차 정제하여 매칭 정확도 향상.
    - **Benchmarking**: 특정 건물 vs **반경 100m 이웃 건물** / **유사 조건(연면적, 연식) 건물** 간의 에너지 효율 비교 분석 알고리즘 구현.

### 📈 대시보드 시각화 (Interactive Dashboard)
> *Reference Code: `dash_multi_graph_app.py`*
- **Tech**: Plotly Dash, Flask
- **주요 기능**:
    - **Multi-Level Drill Down**: `전체 시` -> `구(Gu)` -> `동(Dong)` -> `개별 건물` 단위로 깊이 있는 데이터 탐색 기능.
    - **Dynamic Filtering**: 사용자가 선택한 연도, 월, 건물 유형에 따라 실시간으로 그래프 리렌더링.

---

## 7. 향후 개선 사항 (Future Improvements)
- **보안 강화**: Spring Security를 도입하여 관리자와 일반 사용자 권한 분리 예정.
- **API 확장**: 모바일 앱 확장을 고려하여 RESTful API 구조로 리팩토링.
- **캐싱 전략**: 변동이 적은 건물 정적 데이터에 대한 캐싱(Cache) 적용으로 조회 성능 추가 확보.
