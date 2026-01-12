// --- 전역 변수 -ㄴ--
console.log('Script.js 로드됨 (ECharts 버전, v2 - 오타 수정)');
var map = null;
var _lastState = {
  id: '', type: '', layer: '', coords: '',
  element: null, feature: null, attributes: null,
  ageGroup: '정보 없음', appliedStyle: null
};
var _highlightTimeout = null;
var _HIGHLIGHT_DELAY = 120;
var DEBUG = true;
var VWORLD_API_KEY = '3907B382-CD3D-304B-A82F-C7BFA4286232'; // (참고용)
var _lastAddressRequestId = 0;
// const _dataCache = new Map(); // (사용 안 함, API가 DB에서 직접 가져옴)

// [⭐️ Chart.js] 차트 인스턴스를 저장할 변수
var myHouseChart = null;
var compareChart = null;
var myHouseChartDataCache = null;
var nearbyChartDataCache = null;
var regionChartDataCache = null;
var currentUsageMetric = 'total';
var chartsInitialized = false;
var chartResizeHandlerAttached = false;
var usageToggleHandlerAttached = false;

const USAGE_METRIC_CONFIG = {
  total: {
    valueKey: 'use_total',
    avgKey: 'avg_total',
    datasetLabel: '총 에너지 사용량',
    detailTitle: '선택된 건물의 연도별 총 에너지 사용량',
    compareTitle: '총 에너지 사용량 비교',
    yAxisLabel: '사용량 (kWh 환산)',
    barColor: '#4d7c4d',
    compareColors: ['#3b5f3b', '#7f9f7f', '#b7c9b2']
  },
  electric: {
    valueKey: 'use_electric',
    avgKey: 'avg_electric',
    datasetLabel: '전기 사용량',
    detailTitle: '선택된 건물의 연도별 전기 사용량',
    compareTitle: '전기 사용량 비교',
    yAxisLabel: '전기 사용량 (kWh)',
    barColor: '#f5a623',
    compareColors: ['#f5a623', '#f7c66a', '#fde2b0']
  },
  gas: {
    valueKey: 'use_gas',
    avgKey: 'avg_gas',
    datasetLabel: '가스 사용량',
    detailTitle: '선택된 건물의 연도별 가스 사용량',
    compareTitle: '가스 사용량 비교',
    yAxisLabel: '가스 사용량 (Nm³)',
    barColor: '#3b9dd4',
    compareColors: ['#3b9dd4', '#6fb9e5', '#a0d4f2']
  }
};

var searchMarkers = [];
const SEARCH_MARKER_IMAGE = '/map_img/search-pin.png';
const SEARCH_MARKER_SIZE = { w: 24, h: 24 };
const SEARCH_MAX_MARKERS = 1;
const DEDUPE_EPS = 0.0005;
let _lastSearchRequestId = 0;

// 노후도 색상 팔레트
const AGE_COLOR_MAP = {
  '0~9년': [255, 179, 179, 1],
  '10~20년': [255, 128, 128, 1],
  '20~30년': [255, 77, 77, 1],
  '30년이상': [217, 31, 31, 1],
  '정보 없음': [255, 230, 128, 1],
  '오류': [200, 200, 200, 1]
};

function getAgeColor(ageGroup) {
  return AGE_COLOR_MAP[ageGroup] || AGE_COLOR_MAP['정보 없음'];
}

// (VWorld 하이라이트 관련 함수들 ... 변경 없음)
function buildColorTokens(ageGroup) {
  const rgba = getAgeColor(ageGroup) || AGE_COLOR_MAP['정보 없음'];
  const rgbaString = `rgba(${rgba[0]}, ${rgba[1]}, ${rgba[2]}, ${rgba[3]})`;
  let vwColor = null, wsColor = null, styleExpr = null, cesiumColor = null;
  try {
    if (typeof vw !== 'undefined' && typeof vw.Color === 'function') {
      const r = rgba[0] / 255; const g = rgba[1] / 255; const b = rgba[2] / 255; const a = rgba[3];
      vwColor = new vw.Color(r, g, b, a); wsColor = vwColor.ws3dColor;
    }
    if (typeof vw !== 'undefined' && vw.StyleExpression && typeof vw.StyleExpression.color === 'function') {
      styleExpr = vw.StyleExpression.color(rgbaString);
    }
  } catch (e) { if (DEBUG) console.warn('buildColorTokens vw.Color error', e); }
  try {
    if (typeof Cesium !== 'undefined' && Cesium.Color && typeof Cesium.Color.fromCssColorString === 'function') {
      cesiumColor = Cesium.Color.fromCssColorString(rgbaString);
    }
  } catch (e) { if (DEBUG) console.warn('buildColorTokens Cesium.Color error', e); }
  const colorExpression = `color("${rgbaString}")`;
  const colorProxy = {
    toCssColorString: () => rgbaString,
    evaluateColor: () => {
      if (cesiumColor) return cesiumColor;
      return { toCssColorString: () => rgbaString };
    },
    clone: () => colorProxy, toString: () => rgbaString
  };
  return { rgba, rgbaString, colorExpression, vwColor, wsColor, styleExpr, cesiumColor, colorProxy };
}
function buildHighlightKey(attributes) {
  if (!attributes || typeof attributes !== 'object') return null;
  const key = {};
  if (attributes.__OID__) key.__OID__ = attributes.__OID__;
  if (attributes.TD_ID) key.TD_ID = attributes.TD_ID;
  if (attributes.MODEL_NAME) key.MODEL_NAME = attributes.MODEL_NAME;
  if (attributes.ID) key.ID = attributes.ID;
  if (attributes.FID) key.FID = attributes.FID;
  if (attributes.OBJECTID) key.OBJECTID = attributes.OBJECTID;
  if (attributes.GID) key.GID = attributes.GID;
  if (!key.MODEL_NAME && attributes.NAME) key.NAME = attributes.NAME;
  return Object.keys(key).length ? key : null;
}
function toFeatureCandidate(obj) {
  if (!obj) return null;
  if (typeof obj.setStyle === 'function' || typeof obj.setOptions === 'function') return obj;
  if (obj.feature) return toFeatureCandidate(obj.feature);
  if (Array.isArray(obj.featureInfos) && obj.featureInfos.length) {
    for (const fi of obj.featureInfos) {
      const candidate = toFeatureCandidate(fi?.feature || fi?.element || fi);
      if (candidate) return candidate;
    }
  }
  if (obj.featureInfo) return toFeatureCandidate(obj.featureInfo.feature || obj.featureInfo.element || obj.featureInfo);
  if (obj.element) return toFeatureCandidate(obj.element);
  return null;
}
function getFeatureAttributes(feature, fallbackAttrs) {
  if (!feature && !fallbackAttrs) return null;
  if (feature?.attributes) return feature.attributes;
  if (typeof feature?.getAttributes === 'function') {
    try { return feature.getAttributes(); } catch (e) { if (DEBUG) console.warn('getAttributes error', e); }
  }
  return fallbackAttrs || null;
}
function safeClearHighlight(element, appliedInfo) {
  if (!element) return;
  if (appliedInfo?.method === 'feature.setStyle' && appliedInfo.target) {
    try { safeClearHighlight(appliedInfo.target, appliedInfo.applied); }
    catch (e) { if (DEBUG) console.warn('nested safeClearHighlight error', e); }
  }
  const shouldClearHighlight = !appliedInfo || appliedInfo.method === 'highlightFeatureByKey' || appliedInfo.method === 'highlightFeature';
  if (shouldClearHighlight && typeof element.clearHighlightedFeatures === 'function') {
    try { element.clearHighlightedFeatures(); }
    catch (e) { if (DEBUG) console.warn('clearHighlightedFeatures error', e); }
  }
  if (appliedInfo?.usedSetStyle && typeof element.setStyle === 'function') {
    try { element.setStyle(null); }
    catch (e) { if (DEBUG) console.warn('setStyle reset error', e); }
  }
  if (appliedInfo?.usedSetOptions && typeof element.setOptions === 'function') {
    try { element.setOptions({ outline: false }); }
    catch (e) { if (DEBUG) console.warn('setOptions reset error', e); }
  }
}
function applyElementColorByAge(element, ageGroup, attributes, prebuiltTokens) {
  if (!element) return null;
  const tokens = prebuiltTokens || buildColorTokens(ageGroup);
  let appliedInfo = null;
  const optionColor = tokens.colorExpression;
  if (typeof element.setStyle === 'function') {
    try {
      element.setStyle({
        color: optionColor, outline: true, outlineColor: optionColor,
        material: optionColor, materialColor: optionColor
      });
      appliedInfo = { method: 'setStyle', usedSetStyle: true, ageGroup, color: optionColor };
      return appliedInfo;
    } catch (e) { if (DEBUG) console.warn('setStyle fallback error', e); }
  }
  if (typeof element.setOptions === 'function') {
    try {
      element.setOptions({
        outline: true, outlineColor: optionColor, material: optionColor,
        materialColor: optionColor, color: optionColor, fillColor: optionColor
      });
      appliedInfo = { method: 'setOptions', usedSetOptions: true, ageGroup, color: optionColor };
      return appliedInfo;
    } catch (e) { if (DEBUG) console.warn('setOptions fallback error', e); }
  }
  return appliedInfo;
}
function normalizeAgeValue(rawAge) {
  if (rawAge == null || rawAge === '') return null;
  if (typeof rawAge === 'number') return isFinite(rawAge) ? rawAge : null;
  const parsed = parseFloat(String(rawAge).replace(/[^0-9.\-]/g, ''));
  return isFinite(parsed) ? parsed : null;
}
function getAgeGroup(age) {
  if (age == null || !isFinite(age)) return '정보 없음';
  if (age < 0) return '오류';
  if (age <= 9) return '0~9년';
  if (age <= 20) return '10~20년';
  if (age <= 30) return '20~30년';
  return '30년이상';
}
function rememberSelection(element, feature, attributes) {
  const resolvedElement = element || feature;
  const resolvedFeature = feature || element || null;
  if (!resolvedElement && !resolvedFeature) return;
  if (_lastState.appliedStyle && _lastState.element) {
    safeClearHighlight(_lastState.element, _lastState.appliedStyle);
  }
  _lastState.element = resolvedElement;
  _lastState.feature = resolvedFeature;
  _lastState.attributes = attributes || null;
  _lastState.ageGroup = '정보 없음';
  _lastState.appliedStyle = null;
}
function applySelectionHighlight(ageGroup, explicitFeature) {
  const element = _lastState.element || null;
  const feature = explicitFeature || _lastState.feature || null;
  const attrs = getFeatureAttributes(feature, _lastState.attributes) || _lastState.attributes || null;
  if (!element || !attrs) {
    if (!element) console.warn('⚠️ element가 없어서 하이라이트 불가');
    if (!attrs) console.warn('⚠️ attributes가 없어서 하이라이트 불가');
    return;
  }
  const key = buildHighlightKey(attrs);
  if (!key) {
    console.warn('⚠️ 하이라이트 키 생성 실패 - 개별 건물 식별 불가능');
    return;
  }
  console.log('🔍 하이라이트 시도 - key:', key);
  const tokens = buildColorTokens(ageGroup);
  const highlightColor = tokens.styleExpr || tokens.cesiumColor || tokens.wsColor || tokens.colorProxy;
  const highlightOptions = {
    color: highlightColor,
    highlightColor: highlightColor,
    outline: true,
    outlineColor: highlightColor,
    material: highlightColor
  };
  if (typeof element.highlightFeatureByKey === 'function') {
    try {
      element.highlightFeatureByKey(key, highlightOptions);
      _lastState.appliedStyle = { method: 'highlightFeatureByKey', highlightKey: key, ageGroup };
      _lastState.ageGroup = ageGroup;
      console.log('✅ highlightFeatureByKey 성공!'); return;
    } catch (e) { console.warn('highlightFeatureByKey 실패:', e); }
  }
  if (typeof element.highlightFeature === 'function') {
    try {
      element.highlightFeature(key, highlightOptions);
      _lastState.appliedStyle = { method: 'highlightFeature', highlightKey: key, ageGroup };
      _lastState.ageGroup = ageGroup;
      console.log('✅ highlightFeature 성공!'); return;
    } catch (e) { console.warn('highlightFeature 실패:', e); }
  }
  if (feature) {
    const applied = applyElementColorByAge(feature, ageGroup, attrs, tokens);
    if (applied) {
      _lastState.appliedStyle = Object.assign({}, applied, { method: applied.method || 'feature.setStyle_or_setOptions', target: feature, ageGroup, applied });
      _lastState.feature = feature;
      _lastState.ageGroup = ageGroup;
      return;
    }
  }
  console.error('❌ 개별 건물 하이라이트 실패');
  _lastState.feature = feature || element;
  _lastState.ageGroup = ageGroup;
}
function restorePreviousSelection() {
  if (_lastState.appliedStyle && _lastState.element) {
    safeClearHighlight(_lastState.element, _lastState.appliedStyle);
  }
  _lastState.element = null; 
  _lastState.attributes = null;
  _lastState.ageGroup = '정보 없음'; 
  _lastState.id = '';
  _lastState.coords = ''; 
  _lastState.appliedStyle = null;
  _lastState.element = null; _lastState.attributes = null;
  _lastState.ageGroup = '정보 없음'; _lastState.id = '';
  _lastState.coords = ''; _lastState.appliedStyle = null;
}
function $id(id) { return document.getElementById(id); }
function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// (지도 초기화, 클릭 핸들러 등 ... 변경 없음)
function initializeMap() {
  console.log('지도 초기화 시작...');
  if (typeof vw === 'undefined' || !vw.Map) {
    console.error('VWorld API가 로드되지 않았습니다.'); return false;
  }
  try {
    if (window.map) {
      if (typeof window.map.destroy === 'function') window.map.destroy();
      else if (typeof window.map.dispose === 'function') window.map.dispose();
      window.map = null; map = null;
    }
    var defaultLon = 127.3845; var defaultLat = 36.3504; var defaultHeight = 20000;
    var options = {
      mapId: 'vmap',
      initPosition: new vw.CameraPosition(
        new vw.CoordZ(defaultLon, defaultLat, 2000), new vw.Direction(0, -90, 0)
      ), logo: true, navigation: true
    };
    var newMap = new vw.Map();
    newMap.setOption(options); newMap.setMapId('vmap');
    newMap.setInitPosition(
      new vw.CameraPosition(
        new vw.CoordZ(defaultLon, defaultLat, defaultHeight), new vw.Direction(0, -90, 0)
      )
    );
    newMap.setLogoVisible(true); newMap.setNavigationZoomVisible(true);
    newMap.start();
    map = newMap; window.map = newMap;
    console.log('✅ 지도 생성 완료!');
    setTimeout(attachClickHandler, 1000);
    return true;
  } catch (e) { console.error('지도 생성 오류:', e); return false; }
}
function attachClickHandler() {
  var attempts = 0;
  var interval = setInterval(function() {
    attempts++;
    if (!map) map = window.map;
    if (map) {
      var attached = false;
      if (map.onClick && typeof map.onClick.addEventListener === 'function') {
        try { map.onClick.addEventListener(buildingInfoEvent); attached = true; }
        catch (e) { console.error('클릭 이벤트 부착 실패(onClick):', e); }
      } else if (typeof map.addEventListener === 'function') {
        try {
          var clickEvent = (vw && vw.EventType && vw.EventType.CLICK) ? vw.EventType.CLICK : 'click';
          map.addEventListener(clickEvent, buildingInfoEvent); attached = true;
        } catch (e) { console.error('클릭 이벤트 부착 실패(addEventListener):', e); }
      }
      if (attached) { clearInterval(interval); console.log('✅ 클릭 이벤트 부착 완료!'); return; }
    }
    if (attempts >= 50) { clearInterval(interval); console.error('클릭 핸들러 타임아웃'); }
  }, 200);
}
var buildingInfoEvent = function(windowPosition, ecefPosition, cartographic, modelObject) {
  try {
    if (!modelObject) return;
    const mapElement = modelObject.element || null;
    const feature = toFeatureCandidate(modelObject) || mapElement || null;
    const attributes = getFeatureAttributes(feature, modelObject.attributes);
    if (!mapElement && !feature) return;
    rememberSelection(mapElement, feature, attributes);
    applySelectionHighlight('정보 없음', feature); // (일단 '정보 없음'으로 하이라이트)
    
    // (Epro_map.html의 인라인 스크립트가 담당하므로 이 부분은 생략)
    // const sidebar = $id('mapSidebar');
    // if (sidebar && !sidebar.classList.contains('open')) sidebar.classList.add('open');
    ensureSidebarOpen(); // (사이드바 열기)

    var coordsStr = formatCartographic(cartographic) || '';
    var numericCoords = extractLonLat(cartographic);
    var bIdVal = (attributes && (attributes.MODEL_NAME || attributes.__OID__ || attributes.TD_ID || attributes.ID)) || '';
    
    if (bIdVal !== _lastState.id || coordsStr !== _lastState.coords) {
      _lastState.id = bIdVal; _lastState.coords = coordsStr;
      
      prepareSidebarForData(bIdVal); // (사이드바 '로딩 중...' 표시)
      
      if (numericCoords && isFinite(numericCoords.lon) && isFinite(numericCoords.lat)) {
        // (VWorld 주소 조회 -> 성공 시 fetchDashboardData 호출)
        requestRoadAddressAndData(numericCoords.lon, numericCoords.lat, bIdVal);
      }
    }
  } catch (e) { console.error('buildingInfoEvent error', e); }
};

// --- 지역/주소/POI 검색 ---
// (이전과 동일. VWorld API 프록시 주소를 Spring Boot에 맞게 수정해야 함)
function initRegionSearch() {
  bindSearchControls('regionSearchInput', 'regionSearchBtn');
  bindSearchControls('mapSearchInput', 'mapSearchBtn');
}
function bindSearchControls(inputId, buttonId) {
  const inputEl = $id(inputId); const buttonEl = $id(buttonId);
  if (!inputEl || !buttonEl) return;
  const run = () => performRegionSearch(inputEl);
  buttonEl.type = 'button';
  buttonEl.addEventListener('click', run);
  inputEl.addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
}
async function performRegionSearch(inputEl) {
  const keyword = (inputEl?.value || '').trim();
  if (!keyword) { alert('검색어를 입력해주세요.'); return; }
  await searchRegionAndDisplayResults(keyword);
}
async function searchRegionAndDisplayResults(keyword) {
  const targetMap = map || window.map;
  if (!targetMap) { alert('지도 초기화가 완료되지 않았습니다.'); return; }
  clearSearchMarkers();
  const requestId = ++_lastSearchRequestId;
  const isLatestRequest = () => requestId === _lastSearchRequestId;

  // (Spring Boot VWorld 프록시 API 가정)
  const addrParams = new URLSearchParams({ query: keyword, size: '1', page: '1', type: 'address' });
  let items = await callVworldSearch(addrParams);
  if (!isLatestRequest()) return;
  if (!items || items.length === 0) {
    const poiParams = new URLSearchParams({ query: keyword, size: '1', page: '1', type: 'place' });
    items = await callVworldSearch(poiParams);
  }
  if (!isLatestRequest()) return;
  if (!items || items.length === 0) {
    const fallbackItem = await fallbackGeocodeSearch(keyword);
    if (!isLatestRequest()) return;
    if (fallbackItem) {
      focusMapToSearchResult(targetMap, fallbackItem);
      presentSearchResult(fallbackItem, keyword);
      renderSearchMarkers(targetMap, [fallbackItem]);
      ensureSidebarOpen(); return;
    }
    alert('검색 결과를 찾을 수 없습니다.'); return;
  }
  items = dedupeByCoord(items, DEDUPE_EPS).slice(0, SEARCH_MAX_MARKERS);
  if (!isLatestRequest()) return;
  focusMapToSearchResult(targetMap, items[0]);
  presentSearchResult(items[0], keyword);
  renderSearchMarkers(targetMap, items);
  ensureSidebarOpen();
}
async function callVworldSearch(params) {
  try {
    // (Spring Boot VWorld 프록시 API 가정 - 컨트롤러에 /api/search_address 필요)
    const res = await fetch(`/api/search_address?${params.toString()}`);
    if (!res.ok) { return []; }
    const json = await res.json();
    if (json?.response?.status === 'OK') {
      return json?.response?.result?.items || [];
    }
  } catch (e) { console.error('VWorld 검색 호출 실패:', e); }
  return [];
}
function dedupeByCoord(items, eps) {
  const seen = []; const out = [];
  for (const it of items) {
    const x = Number(it?.point?.x); const y = Number(it?.point?.y);
    if (!isFinite(x) || !isFinite(y)) continue;
    let dup = false;
    for (const [sx, sy] of seen) {
      if (Math.abs(x - sx) <= eps && Math.abs(y - sy) <= eps) { dup = true; break; }
    }
    if (!dup) { seen.push([x, y]); out.push(it); }
  }
  return out;
}
function clearSearchMarkers() {
  if (!Array.isArray(searchMarkers) || !searchMarkers.length) {
    searchMarkers = [];
    return;
  }

  const targetMap = map || window.map;
  searchMarkers.forEach(entry => {
    const marker = entry?.point || entry;
    const markerId = entry?.id || (marker?.getId ? marker.getId() : marker?.id);

    try {
      marker?.setVisible?.(false);
    } catch (err) {
      console.warn('검색 마커 setVisible 실패:', err);
    }

    if (targetMap) {
      if (typeof targetMap.removeObject === 'function') {
        try { targetMap.removeObject(marker); } catch (err) {
          console.warn('검색 마커 removeObject(객체) 실패:', err);
        }
      }
      if (markerId && typeof targetMap.removeObject === 'function') {
        try { targetMap.removeObject(markerId); } catch (err) {
          console.warn('검색 마커 removeObject(ID) 실패:', err);
        }
      }
      if (markerId && typeof targetMap.removeObjectById === 'function') {
        try { targetMap.removeObjectById(markerId); } catch (err) {
          console.warn('검색 마커 removeObjectById 실패:', err);
        }
      }
      if (markerId && typeof targetMap.removeObjectByName === 'function') {
        try { targetMap.removeObjectByName(markerId); } catch (err) {
          console.warn('검색 마커 removeObjectByName 실패:', err);
        }
      }
    }

    try {
      marker?.destroy?.();
    } catch (err) {
      console.warn('검색 마커 destroy 실패:', err);
    }
  });

  searchMarkers = [];
}
function focusMapToSearchResult(targetMap, item) {
  if (!item?.point) return;
  const lon = Number(item.point.x); const lat = Number(item.point.y);
  if (!isFinite(lon) || !isFinite(lat)) return;
  const cameraPosition = new vw.CameraPosition(new vw.CoordZ(lon, lat, 1500), new vw.Direction(0, -90, 0));
  if (typeof targetMap.moveTo === 'function') targetMap.moveTo(cameraPosition);
  const cam = targetMap.getCamera && targetMap.getCamera();
  if (cam?.setPositionAndRotation) cam.setPositionAndRotation(cameraPosition);
  map = targetMap;
}
function renderSearchMarkers(targetMap, items) {
  if (!Array.isArray(items) || items.length === 0) return;
  clearSearchMarkers();

  const item = items[0];
  const mx = Number(item.point?.x); const my = Number(item.point?.y);
  if (!isFinite(mx) || !isFinite(my)) return;

  const point = new vw.geom.Point(new vw.Coord(mx, my));
  point.setImage(SEARCH_MARKER_IMAGE + '?v=20251112', SEARCH_MARKER_SIZE.w, SEARCH_MARKER_SIZE.h);
  point.setName(item.title || '검색결과');
  point.setId('search_marker_0');
  point.setFont('고딕'); point.setFontSize(14);

  const road = item.address?.road || item.address?.roadAddress || '';
  const parcel = item.address?.parcel || item.address?.parcelAddress || '';
  const full = item.address?.full || road || parcel || item.title || '';
  point.set('road', road);
  point.set('parcel', parcel);
  point.set('full', full);
  if (!item.address) item.address = {};
  if (!item.address.full) item.address.full = full;

  point.create();
  if (targetMap && typeof targetMap.addObject === 'function') {
    try { targetMap.addObject(point); }
    catch (err) { console.warn('검색 마커 addObject 실패:', err); }
  }
  point.addEventListener((_windowPosition, _ecef, _carto, featureInfo) => {
    if (!featureInfo) return;
    const markerObj = targetMap.getObjectById(featureInfo.groupId);
    if (!markerObj) return;
    const roadAddr = markerObj.get('road');
    const parcelAddr = markerObj.get('parcel');
    const fullAddr = markerObj.get('full');
    const title = markerObj.getName();
    presentSearchResult({
      point: { x: mx, y: my }, title, address: { road: roadAddr, parcel: parcelAddr, full: fullAddr }
    }, title);
  });

  const markerId = typeof point.getId === 'function' ? point.getId() : point.id || 'search_marker_0';
  searchMarkers.push({ point, id: markerId });
}
function ensureSidebarOpen() {
  // Epro_map.html의 인라인 스크립트가 담당
  const container = $id('mapContainer');
  if (container && !container.classList.contains('map-panel-open')) {
      container.classList.add('map-panel-open');
  }
}
function resetSidebarAdminFields() {
  const ageEl = $id('sidebar_age');
  const purposeEl = $id('sidebar_purpose');
  if (ageEl) ageEl.textContent = '-';
  if (purposeEl) purposeEl.textContent = '-';
}
function prepareSidebarForData() {
  requestAnimationFrame(function() {
    $id('sidebar_address').textContent = '주소 조회 중...';
    $id('sidebar_age').textContent = '노후도 조회 중...';
    $id('sidebar_purpose').textContent = '건물용도 조회 중...';
    $id('sidebar_road').textContent = '-';
    
    initCharts(); 
    showChartLoading('myHouseChart', '에너지 데이터 로딩 중...');
    showChartLoading('compareChart', '비교 데이터 로딩 중...');
  });
}
function presentSearchResult(item, keyword) {
  if (!item) return;
  const lon = Number(item?.point?.x);
  const lat = Number(item?.point?.y);
  if (!isFinite(lon) || !isFinite(lat)) return;

  const label = item?.title || keyword || '검색 결과';
  ensureSidebarOpen();
  prepareSidebarForData();
  updateSidebarWithSearchItem(item, keyword);
  requestRoadAddressAndData(lon, lat, label);
}
function updateSidebarWithSearchItem(item, keyword) {
  const full = item?.address?.full || item?.title || keyword || '';
  const addressEl = $id('sidebar_address');
  if (addressEl && full) addressEl.textContent = full;
  const roadEl = $id('sidebar_road');
  if (roadEl) {
    const roadDetail = item?.address?.full || [item?.address?.road, item?.address?.parcel]
      .filter(Boolean)
      .join(' ');
    roadEl.textContent = roadDetail || '-';
  }
}
async function fallbackGeocodeSearch(keyword) {
  try {
    const params = new URLSearchParams({ query: keyword });
    // (Spring Boot VWorld 프록시 API 가정 - 컨트롤러에 /api/geocode 필요)
    const response = await fetch(`/api/geocode?${params.toString()}`);
    if (!response.ok) return null;
    const data = await response.json();
    if (data?.error) { return null; }
    const result = data?.response?.result;
    const first = Array.isArray(result) ? result[0] : result;
    if (!first?.point) return null;
    const lon = Number(first.point.x); const lat = Number(first.point.y);
    if (!isFinite(lon) || !isFinite(lat)) return null;
    const structure = first.structure || {};
    const road = structure.level4L || structure.level4LC || '';
    const parcel = structure.level5 || structure.level6 || '';
    const full = first.text || [road, parcel].filter(Boolean).join(' ') || keyword;
    return {
      point: { x: lon, y: lat }, title: first.text || keyword,
      address: { road, parcel, full }
    };
  } catch (e) { console.error('Geocode fallback 오류:', e); return null; }
}

// --- 주소 및 데이터 조회 ---
function requestRoadAddressAndData(lon, lat, buildingId) {
  if (!lon || !lat) return;
  
  // (Spring Boot VWorld 프록시 API 가정 - 컨트롤러에 /api/get_address 필요)
  var url = `/api/get_address?lon=${Number(lon).toFixed(9)}&lat=${Number(lat).toFixed(9)}`;
  var requestId = ++_lastAddressRequestId;

  fetch(url)
    .then(res => res.ok ? res.json() : Promise.reject('HTTP ' + res.status))
    .then(data => {
      if (requestId !== _lastAddressRequestId) return; // (이전 요청이면 무시)

      let roadAddress = '';
      let gu = ''; // [⭐️ 추가] '구' 정보 추출
      const responsePayload = data && data.response;
      
      if (responsePayload && responsePayload.status === 'OK') {
        const result = responsePayload.result;
        if (Array.isArray(result) && result.length > 0) {
          const firstResult = result[0];
          roadAddress = firstResult.text || firstResult.structure?.text || '';
          gu = firstResult.structure?.level2 || ''; // VWorld 응답에서 '구' 이름 (예: '서구')
        } else if (result && typeof result === 'object') {
          roadAddress = result.text || '';
          gu = result.structure?.level2 || '';
        }
      }
      $id('sidebar_address').textContent = roadAddress || '주소를 찾을 수 없습니다.';
      updateSidebarWithAddress(responsePayload, roadAddress);

      // [⭐️⭐️⭐️ 핵심 수정 ⭐️⭐️⭐️]
      // VWorld 주소 조회가 성공하면, 이어서 우리 Spring Boot API를 호출
      fetchDashboardData(lon, lat, gu, roadAddress);
    })
    .catch(err => {
      if (requestId !== _lastAddressRequestId) return;
      $id('sidebar_address').textContent = '주소 조회 실패';
      resetSidebarAdminFields();
      
      // (주소 조회 실패해도 에너지 데이터는 시도)
      fetchDashboardData(lon, lat, "정보 없음", '주소 조회 실패');
    });
}


async function fetchDashboardData(lon, lat, gu, roadAddress) {

  try {

    const params = new URLSearchParams({
      lon: lon,
      lat: lat,
      gu: gu || '',
      roadAddress: roadAddress || ''
    });
    const res = await fetch(`/api/dashboard-data?${params.toString()}`);
    
    if (!res.ok) {
        let errText = `데이터 조회 실패: ${res.status}`;
        try { const errData = await res.json(); errText = errData.error; } catch(e){}
        throw new Error(errText);
    }
    
    const data = await res.json();
    
    if (data.error) {
        throw new Error(data.error);
    }

    // 2. 차트 데이터 캐시 및 그리기
    myHouseChartDataCache = data.myHouse || null;
    nearbyChartDataCache = data.nearby || null;
    regionChartDataCache = data.region || null;

    redrawChartsWithCurrentMetric();

    // 3. 사이드바 정보 갱신
    const houseSummary = data.myHouse || {};
    const rawAge = houseSummary.age;
    const ageNumeric = rawAge != null && rawAge !== '' ? Number(rawAge) : null;
    const ageGroup = houseSummary.ageCategory || '정보 없음';
    const ageText = (ageNumeric != null && isFinite(ageNumeric))
      ? `${ageNumeric.toFixed(1)} 년 (${ageGroup})`
      : (ageGroup || '정보 없음');

    updateSidebarAgeDisplay(ageGroup, ageText);
    updateSidebarPurposeDisplay(houseSummary.purpose);

    applySelectionHighlight(ageGroup);

  } catch (e) {
    console.error('fetchDashboardData (Spring API) 오류', e);
    myHouseChartDataCache = null;
    nearbyChartDataCache = null;
    regionChartDataCache = null;

    showChartError('myHouseChart', e.message || '데이터 로드 실패');
    showChartError('compareChart', '데이터 로드 실패');

    updateSidebarAgeDisplay('오류', '조회 실패');
    updateSidebarPurposeDisplay('조회 실패');
    applySelectionHighlight('오류');
  }
}

// (이전 'fetchDataFromCoords' 함수는 삭제됨 - fetchDashboardData가 대체함)


// --- 하이라이트 & 좌표 유틸 ---
function debouncedHighlight(mapElement, attributes) {
  if (_highlightTimeout) clearTimeout(_highlightTimeout);
  _highlightTimeout = setTimeout(function() {
    try { if (mapElement && typeof mapElement.highlightFeatureByKey === 'function') mapElement.highlightFeatureByKey(attributes); }
    catch (e) {}
  }, _HIGHLIGHT_DELAY);
}
function formatCartographic(cartographic) {
  if (!cartographic) return '';
  var lon, lat, h;
  if (Array.isArray(cartographic)) { lon = cartographic[0]; lat = cartographic[1]; h = cartographic[2]; }
  else if (typeof cartographic === 'object') {
    lon = cartographic.longitude || cartographic.lon || cartographic.x;
    lat = cartographic.latitude || cartographic.lat || cartographic.y;
    h = cartographic.height || cartographic.z;
  }
  function toDegOrKeep(v) {
    if (v == null || !isFinite(v)) return null;
    return Math.abs(v) <= 2 * Math.PI ? (v * 180 / Math.PI).toFixed(6) : Number(v).toFixed(6);
  }
  var lonD = toDegOrKeep(lon); var latD = toDegOrKeep(lat);
  if (!lonD || !latD) return '';
  return lonD + ', ' + latD + (h ? (' (h:' + Number(h).toFixed(2) + ')') : '');
}
function extractLonLat(cartographic) {
  if (!cartographic) return null;
  var lon, lat, h;
  if (Array.isArray(cartographic)) { lon = cartographic[0]; lat = cartographic[1]; h = cartographic[2]; }
  else if (typeof cartographic === 'object') {
    lon = cartographic.longitude || cartographic.lon || cartographic.x;
    lat = cartographic.latitude || cartographic.lat || cartographic.y;
    h = cartographic.height || cartographic.z;
  }
  if (lon == null || lat == null) return null;
  function toDeg(v) {
    if (v == null || !isFinite(v)) return null;
    return Math.abs(v) <= 2 * Math.PI ? v * 180 / Math.PI : v;
  }
  return { lon: toDeg(lon), lat: toDeg(lat), height: (h != null && isFinite(h)) ? Number(h) : null };
}
function buildDetailText(structure, firstResult) {
  const parts = [];
  function push(v) {
    if (!v) return; const t = String(v).trim();
    if (t && !parts.includes(t)) parts.push(t);
  }
  const s1 = firstResult?.structure || {};
  push(structure.level4A || s1.level4A);
  push(structure.detail || s1.detail);
  push(firstResult?.detail);
  push(structure.level6 || s1.level6);
  push(structure.buildingName || s1.buildingName);
  return parts.join(' ');
}
function updateSidebarWithAddress(response, fallbackRoadAddress) {
  const refined = response?.refined || {};
  const results = response?.result;
  const firstResult = Array.isArray(results) ? results[0] : results;
  const structure = refined.structure || firstResult?.structure || {};
  const fullText = refined.text || firstResult?.text || fallbackRoadAddress;
  const addressEl = $id('sidebar_address');
  const roadEl = $id('sidebar_road');
  if (addressEl) addressEl.textContent = fullText || fallbackRoadAddress || '주소 정보를 찾을 수 없습니다.';
  if (roadEl) {
    const detailText = buildDetailText(structure, firstResult);
    const roadDetail = detailText || refined.roadAddress || structure.level4L || structure.level4LC || fallbackRoadAddress;
    roadEl.textContent = roadDetail || '-';
  }
}
function resetSidebarAdminFields() {
  const roadEl = $id('sidebar_road');
  if (roadEl) roadEl.textContent = '-';
}

function updateSidebarAgeDisplay(ageGroup, displayText) {
  const ageEl = $id('sidebar_age');
  if (!ageEl) return;
  if (displayText) {
    ageEl.textContent = displayText;
  } else if (ageGroup) {
    ageEl.textContent = ageGroup;
  } else {
    ageEl.textContent = '정보 없음';
  }
}

function updateSidebarPurposeDisplay(purposeText) {
  const purposeEl = $id('sidebar_purpose');
  if (!purposeEl) return;
  purposeEl.textContent = purposeText || '정보 없음';
}

// --- 페이지 로드 ---
window.addEventListener('load', function() {
  console.log('페이지 로드 완료');
  // initMapSidebar(); (Epro_map.html의 인라인 스크립트가 담당)
  initRegionSearch();
  initCharts(); // [⭐️ Chart.js] 차트 인스턴스 생성
  
  var attempts = 0;
  var interval = setInterval(function() {
    attempts++;
    if (typeof vw !== 'undefined' && typeof vw.Map === 'function') {
      clearInterval(interval);
      console.log('VWorld API 로드 완료');
      // Epro_map.html은 즉시 초기화, Epro_dashboard.html은 vmap ID가 있음
      if ($id('vmap')) {
        setTimeout(function() { initializeMap(); }, 500);
      }
    } else if (attempts >= 50) {
      clearInterval(interval);
      console.error('VWorld API 로드 타임아웃');
      if ($id('vmap')) { // 지도 페이지에서만 경고
          alert('지도를 로드할 수 없습니다. 페이지를 새로고침해주세요.');
      }
    }
  }, 200);
});


/* ========================================================== */
/* ⭐️ Chart.js 그래프 렌더링 유틸리티 ⭐️ */
/* ========================================================== */

function initCharts() {
  const myHouseCanvas = $id('myHouseChartCanvas');
  if (myHouseCanvas && !myHouseChart) {
    const ctx = myHouseCanvas.getContext('2d');
    if (ctx) {
      myHouseChart = new Chart(ctx, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 700,
            easing: 'easeOutQuart'
          },
          plugins: {
            legend: { display: false },
            title: { display: false, text: '' },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(62, 94, 62, 0.85)',
              titleColor: '#ffffff',
              bodyColor: '#f2f8f1',
              borderColor: 'rgba(62, 94, 62, 0.4)',
              borderWidth: 1
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#3b5f3b' }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(77, 124, 77, 0.08)',
                drawBorder: false
              },
              ticks: {
                color: '#3b5f3b',
                callback: value => formatUsageTick(value)
              },
              title: { display: false, text: '' }
            }
          }
        }
      });
    }
  }

  const compareCanvas = $id('compareChartCanvas');
  if (compareCanvas && !compareChart) {
    const ctx = compareCanvas.getContext('2d');
    if (ctx) {
      compareChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 650,
            easing: 'easeOutCubic'
          },
          interaction: {
            mode: 'nearest',
            intersect: false
          },
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: '#2f4b2f',
                usePointStyle: true,
                padding: 16
              }
            },
            title: { display: false, text: '' },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(62, 94, 62, 0.85)',
              titleColor: '#ffffff',
              bodyColor: '#f2f8f1',
              borderColor: 'rgba(62, 94, 62, 0.4)',
              borderWidth: 1
            }
          },
          scales: {
            x: {
              grid: {
                color: 'rgba(77, 124, 77, 0.05)',
                lineWidth: 0.7
              },
              ticks: { color: '#3b5f3b' }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(77, 124, 77, 0.08)',
                lineWidth: 0.8,
                drawBorder: false
              },
              ticks: {
                color: '#3b5f3b',
                callback: value => formatUsageTick(value)
              },
              title: { display: false, text: '' }
            }
          }
        }
      });
    }
  }

  if (!chartResizeHandlerAttached) {
    window.addEventListener('resize', function() {
      if (myHouseChart) myHouseChart.resize();
      if (compareChart) compareChart.resize();
    });
    chartResizeHandlerAttached = true;
  }

  const toggleWrap = $id('usageMetricToggle');
  if (toggleWrap && !usageToggleHandlerAttached) {
    toggleWrap.addEventListener('click', function(e) {
      const btn = e.target.closest('button[data-usage-metric]');
      if (!btn) return;
      const metric = btn.getAttribute('data-usage-metric');
      if (!metric || metric === currentUsageMetric) return;
      currentUsageMetric = metric;
      Array.from(toggleWrap.querySelectorAll('button')).forEach(b => {
        b.classList.toggle('is-active', b === btn);
      });
      const graphContainer = $id('sidebar_graphs');
      if (graphContainer) {
        graphContainer.classList.add('is-switching');
        setTimeout(() => graphContainer.classList.remove('is-switching'), 600);
      }
      redrawChartsWithCurrentMetric();
    });
    usageToggleHandlerAttached = true;
  }

  const toggleBtn = $id('mapSidebarToggleBtn');
  if (toggleBtn && !toggleBtn.__chartResizeAttached) {
    toggleBtn.addEventListener('click', function() {
      setTimeout(function() {
        if (myHouseChart) myHouseChart.resize();
        if (compareChart) compareChart.resize();
      }, 400);
    });
    toggleBtn.__chartResizeAttached = true;
  }

  chartsInitialized = !!myHouseChart && !!compareChart;

  if (chartsInitialized && myHouseChartDataCache) {
    redrawChartsWithCurrentMetric();
  }
}

/**
 * 차트 로딩 중 메시지 표시
 */
function showChartLoading(chartId, text) {
  const chart = chartId === 'myHouseChart' ? myHouseChart : compareChart;
  toggleChartPlaceholder(chartId, text || '로딩 중...');
  if (chart) {
    chart.data.labels = [];
    chart.data.datasets = [];
    chart.update('none');
  }
}
function showChartError(chartId, text) {
  const chart = chartId === 'myHouseChart' ? myHouseChart : compareChart;
  toggleChartPlaceholder(chartId, text || '데이터 로드 실패');
  if (chart) {
    chart.data.labels = [];
    chart.data.datasets = [];
    chart.update('none');
  }
}

function toggleChartPlaceholder(chartId, message) {
  const container = $id(chartId);
  if (!container) return;
  const placeholder = container.querySelector('.graph-placeholder');
  const canvas = container.querySelector('canvas');
  if (!placeholder) return;
  if (message) {
    placeholder.textContent = message;
    placeholder.style.display = 'flex';
    if (canvas) canvas.style.visibility = 'hidden';
  } else {
    placeholder.style.display = 'none';
    if (canvas) canvas.style.visibility = 'visible';
  }
}

function formatUsageTick(value) {
  if (value == null || !isFinite(value)) return '';
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return (value / 1_000_000).toFixed(1) + 'M';
  if (abs >= 1_000) return (value / 1_000).toFixed(1) + 'k';
  if (abs >= 1) return Number(value.toFixed(0)).toLocaleString();
  return value.toFixed(2);
}

function numberOrNull(value) {
  if (value == null || value === '') return null;
  const num = Number(value);
  return isFinite(num) ? num : null;
}

function averageValues(values) {
  const filtered = values.filter(v => v != null && isFinite(v));
  if (!filtered.length) return null;
  const sum = filtered.reduce((acc, val) => acc + val, 0);
  return sum / filtered.length;
}

function resolveValueCaseInsensitive(obj, key) {
  if (!obj || !key) return undefined;
  if (Object.prototype.hasOwnProperty.call(obj, key)) return obj[key];
  const upper = key.toUpperCase();
  if (Object.prototype.hasOwnProperty.call(obj, upper)) return obj[upper];
  const lower = key.toLowerCase();
  if (Object.prototype.hasOwnProperty.call(obj, lower)) return obj[lower];
  return undefined;
}

function buildSeriesMap(rows, valueKey) {
  const series = new Map();
  if (!Array.isArray(rows)) return series;
  rows.forEach(row => {
    if (!row) return;
    const yearRaw = resolveValueCaseInsensitive(row, 'year') ?? resolveValueCaseInsensitive(row, 'date');
    if (yearRaw == null || yearRaw === '') return;
    const valueRaw = resolveValueCaseInsensitive(row, valueKey);
    const value = numberOrNull(valueRaw);
    if (value == null) return;
    const year = String(yearRaw);
    series.set(year, value);
  });
  return series;
}

function mergeSeriesLabels(...maps) {
  const labelSet = new Set();
  maps.forEach(map => {
    if (!map) return;
    map.forEach((_, key) => {
      if (key != null) labelSet.add(String(key));
    });
  });
  return Array.from(labelSet).sort((a, b) => Number(a) - Number(b));
}

function redrawChartsWithCurrentMetric() {
  if (!myHouseChart || !compareChart) {
    if (!chartsInitialized) initCharts();
    if (!myHouseChart || !compareChart) return;
  }

  const metricConfig = USAGE_METRIC_CONFIG[currentUsageMetric] || USAGE_METRIC_CONFIG.total;
  const houseData = myHouseChartDataCache;

  if (!houseData || !Array.isArray(houseData.energyData) || houseData.energyData.length === 0) {
    showChartLoading('myHouseChart', '해당 건물의 에너지 데이터가 없습니다.');
  } else {
    const labels = houseData.energyData.map(item => String(item.year || item.YEAR || item.date || item.DATE || ''));
    const datasetValues = houseData.energyData.map(item => numberOrNull(item[metricConfig.valueKey]));

    toggleChartPlaceholder('myHouseChart', null);

    myHouseChart.data.labels = labels;
    myHouseChart.data.datasets = [{
      label: metricConfig.datasetLabel,
      data: datasetValues,
      backgroundColor: metricConfig.barColor,
      borderRadius: 6
    }];

    myHouseChart.options.plugins.title.display = true;
    myHouseChart.options.plugins.title.text = metricConfig.detailTitle;
    myHouseChart.options.scales.y.title.display = true;
    myHouseChart.options.scales.y.title.text = metricConfig.yAxisLabel;
    myHouseChart.update('none');
  }

  const buildingType = (houseData && houseData.purpose) ? houseData.purpose : '주택';
  const ageLabel = (houseData && houseData.ageCategory) ? houseData.ageCategory : '';
  const regionName = (regionChartDataCache && regionChartDataCache.region_name) ? regionChartDataCache.region_name : '지역 평균';
  const regionPurpose = (regionChartDataCache && regionChartDataCache.purpose_filter)
    ? String(regionChartDataCache.purpose_filter).trim()
    : '';
  const regionSeriesRows = Array.isArray(regionChartDataCache?.series) ? regionChartDataCache.series : [];

  const houseSeriesMap = buildSeriesMap(houseData?.energyData, metricConfig.valueKey);
  const regionSeriesMap = buildSeriesMap(regionSeriesRows, metricConfig.valueKey);

  const compareLabels = mergeSeriesLabels(houseSeriesMap, regionSeriesMap);
  if (!compareLabels.length) {
    showChartLoading('compareChart', '비교 데이터가 없습니다.');
    return;
  }

  const colors = metricConfig.compareColors || ['#3b5f3b', '#7f9f7f'];
  const regionLabel = regionPurpose ? `${regionName} (${regionPurpose})` : regionName;
  const datasets = [
    { label: '내 주택', map: houseSeriesMap, color: colors[0] || '#3b5f3b' },
    { label: regionLabel, map: regionSeriesMap, color: colors[1] || '#7f9f7f' }
  ].map(({ label, map, color }) => ({
    label,
    data: compareLabels.map(year => (map.has(year) ? map.get(year) : null)),
    borderColor: color,
    backgroundColor: color,
    borderWidth: 2,
    fill: false,
    spanGaps: true,
    tension: 0.25,
    pointRadius: 3,
    pointHoverRadius: 5,
    pointBackgroundColor: color,
    pointBorderColor: color
  }));

  const hasData = datasets.some(ds => ds.data.some(value => value != null));
  if (!hasData) {
    showChartLoading('compareChart', '비교 데이터가 없습니다.');
    return;
  }

  toggleChartPlaceholder('compareChart', null);
  compareChart.data.labels = compareLabels;
  compareChart.data.datasets = datasets;
  compareChart.options.plugins.title.display = true;
  compareChart.options.plugins.title.text = metricConfig.compareTitle;
  compareChart.options.scales.y.title.display = true;
  compareChart.options.scales.y.title.text = metricConfig.yAxisLabel;
  compareChart.update('none');
}