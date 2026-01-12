// --- 전역 변수 ---
console.log('Script.js 로드됨');
var map = null;
var _lastState = { id: '', type: '', layer: '', coords: '' };
var _highlightTimeout = null;
var _HIGHLIGHT_DELAY = 120;
var DEBUG = true;
var VWORLD_API_KEY = '3907B382-CD3D-304B-A82F-C7BFA4286232';
var _lastAddressRequestId = 0;
const _dataCache = new Map();
var searchMarkers = [];
var activeSearchPopup = null;
const SEARCH_MARKER_IMAGE = '/static/pin.png';

const popupRefs = {
  container: null,
  closeBtn: null,
  fields: {}
};

function $id(id) {
  return document.getElementById(id);
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function fallbackPoiSearch(keyword) {
  try {
    const params = new URLSearchParams({
      keyword,
      size: '5',
      type: 'place',
      category: 'POI',
      domain: 'poi'
    });

    const response = await fetch(`/api/search_address?${params.toString()}`);
    if (!response.ok) return null;

    const data = await response.json();
    if (data?.error) {
      console.warn('POI 검색 프록시 오류:', data.error);
      return null;
    }

    const items = data?.response?.result?.items;
    if (!Array.isArray(items) || !items.length) return null;

    const first = items[0];
    if (!first?.point) return null;

    const lon = Number(first.point.x);
    const lat = Number(first.point.y);
    if (!isFinite(lon) || !isFinite(lat)) return null;

    const addr = first.address || {};
    const road = addr.road || addr.roadAddress || '';
    const parcel = addr.parcel || addr.parcelAddress || '';
    const full = addr.full || first.title || [road, parcel].filter(Boolean).join(' ') || keyword;

    return {
      point: { x: lon, y: lat },
      title: first.title || keyword,
      address: {
        road,
        parcel,
        full
      }
    };
  } catch (e) {
    console.error('POI fallback 오류:', e);
    return null;
  }
}

function $id(id) {
  return document.getElementById(id);
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// --- 지도 초기화 (간단 버전) ---
function initializeMap() {
  console.log('지도 초기화 시작...');

  if (typeof vw === 'undefined' || !vw.Map) {
    console.error('VWorld API가 로드되지 않았습니다.');
    return false;
  }

  try {
    // 기존 지도 제거
    if (window.map) {
      if (typeof window.map.destroy === 'function') {
        window.map.destroy();
      } else if (typeof window.map.dispose === 'function') {
        window.map.dispose();
      }
      window.map = null;
      map = null;
    }

    var defaultLon = 127.3845;
    var defaultLat = 36.3504;
    var defaultHeight = 20000;

    var options = {
      mapId: 'vmap',
      initPosition: new vw.CameraPosition(
        new vw.CoordZ(defaultLon, defaultLat, 2000),
        new vw.Direction(0, -90, 0)
      ),
      logo: true,
      navigation: true
    };

    var newMap = new vw.Map();
    newMap.setOption(options);
    newMap.setMapId('vmap');
    newMap.setInitPosition(
      new vw.CameraPosition(
        new vw.CoordZ(defaultLon, defaultLat, defaultHeight),
        new vw.Direction(0, -90, 0)
      )
    );

    newMap.setLogoVisible(true);
    newMap.setNavigationZoomVisible(true);
    newMap.start();

    map = newMap;
    window.map = newMap;

    console.log('✅ 지도 생성 완료!');

    // 클릭 핸들러 부착
    setTimeout(attachClickHandler, 1000);

    return true;
  } catch (e) {
    console.error('지도 생성 오류:', e);
    return false;
  }
}

// --- 클릭 핸들러 부착 ---
function attachClickHandler() {
  var attempts = 0;
  var interval = setInterval(function() {
    attempts++;

    if (!map) map = window.map;

    if (map) {
      var attached = false;

      if (map.onClick && typeof map.onClick.addEventListener === 'function') {
        try {
          map.onClick.addEventListener(buildingInfoEvent);
          attached = true;
        } catch (e) {
          console.error('클릭 이벤트 부착 실패(onClick):', e);
        }
      } else if (typeof map.addEventListener === 'function') {
        try {
          var clickEvent =
            (vw && vw.EventType && vw.EventType.CLICK) ? vw.EventType.CLICK : 'click';
          map.addEventListener(clickEvent, buildingInfoEvent);
          attached = true;
        } catch (e) {
          console.error('클릭 이벤트 부착 실패(addEventListener):', e);
        }
      } else if (map.getEventManager && typeof map.getEventManager === 'function') {
        try {
          var manager = map.getEventManager();
          if (manager && typeof manager.addEventListener === 'function') {
            var managerClickEvent =
              (vw && vw.EventType && vw.EventType.CLICK) ? vw.EventType.CLICK : 'click';
            manager.addEventListener(managerClickEvent, buildingInfoEvent);
            attached = true;
          }
        } catch (e) {
          console.error('클릭 이벤트 부착 실패(eventManager):', e);
        }
      }

      if (attached) {
        clearInterval(interval);
        console.log('✅ 클릭 이벤트 부착 완료!');
        return;
      }
    }

    if (attempts >= 50) {
      clearInterval(interval);
      console.error('클릭 핸들러 타임아웃');
    }
  }, 200);
}

// --- 클릭 이벤트 핸들러 ---
var buildingInfoEvent = function(windowPosition, ecefPosition, cartographic, modelObject) {
  try {
    if (!modelObject) return;

    var mapElement = modelObject.element;
    var attributes = modelObject.attributes;
    if (!attributes || !mapElement) return;

    // 사이드바 열기
    const sidebar = $id('mapSidebar');
    if (sidebar && !sidebar.classList.contains('open')) {
      sidebar.classList.add('open');
    }

    debouncedHighlight(mapElement, attributes);

    var coordsStr = formatCartographic(cartographic) || '';
    var numericCoords = extractLonLat(cartographic);
    var bIdVal = attributes.MODEL_NAME || '';

    if (bIdVal !== _lastState.id || coordsStr !== _lastState.coords) {
      _lastState.id = bIdVal;
      _lastState.coords = coordsStr;

      resetPopupDetails(bIdVal);

      requestAnimationFrame(function() {
        const addressEl = $id('sidebar_address');
        const ageEl = $id('sidebar_age');
        const idEl = $id('sidebar_id');
        const purposeEl = $id('sidebar_purpose');
        const heightEl = $id('sidebar_height');
        const floorsEl = $id('sidebar_floors');
        const structureEl = $id('sidebar_structure');
        const coordsEl = $id('sidebar_coords');

        if (addressEl) addressEl.textContent = '조회 중...';
        if (ageEl) ageEl.textContent = '조회 중...';
        if (idEl) idEl.textContent = bIdVal || '정보 없음';
        if (purposeEl) purposeEl.textContent = '조회 중...';
        if (heightEl) heightEl.textContent = '-';
        if (floorsEl) floorsEl.textContent = '-';
        if (structureEl) structureEl.textContent = '-';
        if (coordsEl) coordsEl.textContent = coordsStr || '-';
      });

      if (numericCoords && isFinite(numericCoords.lon) && isFinite(numericCoords.lat)) {
        requestRoadAddressAndData(numericCoords.lon, numericCoords.lat, bIdVal);
      }
    }
  } catch (e) {
    console.error('buildingInfoEvent error', e);
  }
};

// --- 사이드바 토글 ---
function initMapSidebar() {
  const toggleBtn = $id('toggleMapSidebar');
  const sidebar = $id('mapSidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });
  }
}

// --- 지역 검색 ---
function initRegionSearch() {
  bindSearchControls('regionSearchInput', 'regionSearchBtn');
  bindSearchControls('mapSearchInput', 'mapSearchBtn');
}

function bindSearchControls(inputId, buttonId) {
  const inputEl = $id(inputId);
  const buttonEl = $id(buttonId);

  if (!inputEl || !buttonEl) return;

  const runSearch = () => performRegionSearch(inputEl);

  buttonEl.addEventListener('click', runSearch);
  inputEl.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') runSearch();
  });
}

async function performRegionSearch(inputEl) {
  if (!inputEl) return;

  const query = inputEl.value.trim();
  if (!query) {
    alert('검색어를 입력해주세요.');
    return;
  }

  await searchRegionAndDisplayResults(query);
}

async function searchRegionAndDisplayResults(keyword) {
  var targetMap = map || window.map;
  if (!targetMap) {
    alert('지도 초기화가 완료되지 않았습니다. 잠시 후 다시 시도해주세요.');
    return;
  }

  clearSearchMarkers();

  const params = new URLSearchParams({
    keyword,
    size: '10',
    page: '1',
    type: 'address',
    data: 'LT_C_AISBR'
  });

  const url = `/api/search_address?${params.toString()}`;

  let json;
  try {
    const response = await fetch(url);
    json = await response.json();
  } catch (e) {
    console.error('지역 검색 오류:', e);
  }

  let items = [];
  if (json?.response?.status === 'OK') {
    items = json.response.result?.items || [];
  } else if (json?.error) {
    console.warn('검색 API 오류:', json.error);
  }

  if (!Array.isArray(items)) items = [];

  if (!items.length) {
    const poiItem = await fallbackPoiSearch(keyword);
    if (poiItem) {
      focusMapToSearchResult(targetMap, poiItem);
      presentSearchResult(poiItem, keyword);
      renderSearchMarkers(targetMap, [poiItem]);
      ensureSidebarOpen();
      return;
    }

    const fallbackItem = await fallbackGeocodeSearch(keyword);
    if (fallbackItem) {
      focusMapToSearchResult(targetMap, fallbackItem);
      presentSearchResult(fallbackItem, keyword);
      renderSearchMarkers(targetMap, [fallbackItem]);
      ensureSidebarOpen();
      return;
    }

    alert('검색 결과를 찾을 수 없습니다.');
    return;
  }

  focusMapToSearchResult(targetMap, items[0]);
  presentSearchResult(items[0], keyword);
  renderSearchMarkers(targetMap, items);
  ensureSidebarOpen();
}

function clearSearchMarkers() {
  if (!Array.isArray(searchMarkers) || !searchMarkers.length) return;
  searchMarkers.forEach(function(marker) {
    try {
      if (marker && typeof marker.destroy === 'function') {
        marker.destroy();
      }
    } catch (e) {}
  });
  searchMarkers = [];

  if (activeSearchPopup && typeof activeSearchPopup.destroy === 'function') {
    try {
      activeSearchPopup.destroy();
    } catch (e) {}
  }
  activeSearchPopup = null;
}

function focusMapToSearchResult(targetMap, item) {
  if (!item?.point) return;
  const lon = Number(item.point.x);
  const lat = Number(item.point.y);
  if (!isFinite(lon) || !isFinite(lat)) return;

  const cameraPosition = new vw.CameraPosition(
    new vw.CoordZ(lon, lat, 1500),
    new vw.Direction(0, -90, 0)
  );

  if (typeof targetMap.moveTo === 'function') {
    targetMap.moveTo(cameraPosition);
  }

  const camera = targetMap.getCamera && targetMap.getCamera();
  if (camera && typeof camera.setPositionAndRotation === 'function') {
    camera.setPositionAndRotation(cameraPosition);
  }

  map = targetMap;
}

function renderSearchMarkers(targetMap, items) {
  if (!Array.isArray(items)) return;

  items.forEach(function(item, index) {
    const mx = Number(item.point?.x);
    const my = Number(item.point?.y);
    if (!isFinite(mx) || !isFinite(my)) return;

    var point = new vw.geom.Point(new vw.Coord(mx, my));
    point.setImage(SEARCH_MARKER_IMAGE, 10, 10);
    point.setName(item.title || `검색결과 ${index + 1}`);
    point.setFont('고딕');
    point.setId('search_marker_' + index);
    point.setFontSize(14);
    const road = item.address?.road || '';
    const parcel = item.address?.parcel || '';
    const full = item.address?.full || road || parcel || item.title || '';
    point.set('road', road);
    point.set('parcel', parcel);
    point.set('full', full);

    if (!item.address) item.address = {};
    if (!item.address.full) item.address.full = full;

    point.create();

    point.addEventListener(function(windowPosition, ecefPosition, cartographic, featureInfo) {
      if (!featureInfo) return;

      var markerObj = targetMap.getObjectById(featureInfo.groupId);
      if (!markerObj) return;

      var road = markerObj.get('road');
      var parcel = markerObj.get('parcel');
      var full = markerObj.get('full');
      var title = markerObj.getName();

      var html = `<div class="search-popup">`
        + (full ? `<div class="popup-road">${escapeHtml(full)}</div>` : '')
        + (road && parcel ? `<div class="popup-detail">도로명: ${escapeHtml(road)}<br>지번: ${escapeHtml(parcel)}</div>` : '')
        + `</div>`;

      if (activeSearchPopup && typeof activeSearchPopup.destroy === 'function') {
        try {
          activeSearchPopup.destroy();
        } catch (e) {}
      }

      activeSearchPopup = new vw.Popup(
        'search_popup',
        'vmap',
        escapeHtml(title || '검색 결과'),
        html,
        220,
        110,
        windowPosition.x,
        windowPosition.y
      );

      activeSearchPopup.create();

      presentSearchResult({
        point: { x: mx, y: my },
        title: title,
        address: { road: road, parcel: parcel, full: full }
      }, title);
    });

    searchMarkers.push(point);
  });
}

function ensureSidebarOpen() {
  const sidebar = $id('mapSidebar');
  if (sidebar && !sidebar.classList.contains('open')) {
    sidebar.classList.add('open');
  }
}

function presentSearchResult(item, keyword) {
  if (!item) return;

  const lon = Number(item?.point?.x);
  const lat = Number(item?.point?.y);
  if (!isFinite(lon) || !isFinite(lat)) return;

  const label = item?.title || keyword || '검색 결과';

  resetPopupDetails(label);

  if (popupRefs.fields?.title) {
    popupRefs.fields.title.textContent = label ? `검색 결과 (${label})` : '검색 결과';
  }

  updateSidebarWithSearchItem(item, keyword);

  requestAnimationFrame(function() {
    const ageEl = $id('sidebar_age');
    const idEl = $id('sidebar_id');
    const purposeEl = $id('sidebar_purpose');
    const heightEl = $id('sidebar_height');
    const floorsEl = $id('sidebar_floors');
    const structureEl = $id('sidebar_structure');

    if (ageEl) ageEl.textContent = '조회 중...';
    if (purposeEl) purposeEl.textContent = '조회 중...';
    if (heightEl) heightEl.textContent = '-';
    if (floorsEl) floorsEl.textContent = '-';
    if (structureEl) structureEl.textContent = '-';
    if (idEl) idEl.textContent = label || '검색 결과';
  });

  requestRoadAddressAndData(lon, lat, label);
}

function updateSidebarWithSearchItem(item, keyword) {
  const full = item?.address?.full || item?.title || keyword || '';
  const lon = Number(item?.point?.x);
  const lat = Number(item?.point?.y);

  const addressEl = $id('sidebar_address');
  if (addressEl && full) addressEl.textContent = full;

  const coordsEl = $id('sidebar_coords');
  if (coordsEl && isFinite(lon) && isFinite(lat)) {
    coordsEl.textContent = `${lon.toFixed(6)}, ${lat.toFixed(6)}`;
  }

  if (popupRefs?.fields?.fullAddress && full) {
    popupRefs.fields.fullAddress.textContent = full;
  }
}

async function fallbackGeocodeSearch(keyword) {
  try {
    const params = new URLSearchParams({ query: keyword });
    const response = await fetch(`/api/geocode?${params.toString()}`);
    if (!response.ok) return null;

    const data = await response.json();
    if (data?.error) {
      console.warn('지오코딩 프록시 오류:', data.error);
      return null;
    }

    const result = data?.response?.result;
    const first = Array.isArray(result) ? result[0] : result;
    if (!first?.point) return null;

    const lon = Number(first.point.x);
    const lat = Number(first.point.y);
    if (!isFinite(lon) || !isFinite(lat)) return null;

    const structure = first.structure || {};
    const road = structure.level4L || structure.level4LC || '';
    const parcel = structure.level5 || structure.level6 || '';
    const full = first.text || [road, parcel].filter(Boolean).join(' ') || keyword;

    return {
      point: { x: lon, y: lat },
      title: first.text || keyword,
      address: {
        road,
        parcel,
        full
      }
    };
  } catch (e) {
    console.error('Geocode fallback 오류:', e);
    return null;
  }
}

// --- 주소 및 데이터 조회 ---
function requestRoadAddressAndData(lon, lat, buildingId) {
  if (!lon || !lat) return;

  var url = `/api/get_address?lon=${Number(lon).toFixed(9)}&lat=${Number(lat).toFixed(9)}`;
  var requestId = ++_lastAddressRequestId;

  fetch(url)
    .then(res => res.ok ? res.json() : Promise.reject('HTTP ' + res.status))
    .then(data => {
      if (requestId !== _lastAddressRequestId) return;

      let roadAddress = '';
      const responsePayload = data && data.response;
      if (responsePayload && responsePayload.status === 'OK') {
        const result = responsePayload.result;
        if (Array.isArray(result) && result.length > 0) {
          const firstResult = result[0];
          roadAddress = firstResult.text || firstResult.structure?.text || '';
        } else if (result && typeof result === 'object') {
          roadAddress = result.text || '';
        }
      }

      const addressEl = $id('sidebar_address');
      if (addressEl) addressEl.textContent = roadAddress || '주소를 찾을 수 없습니다.';

      updatePopupWithAddress(responsePayload, roadAddress);

      fetchBuildingData(lon, lat, buildingId);
    })
    .catch(err => {
      if (requestId !== _lastAddressRequestId) return;
      const addressEl = $id('sidebar_address');
      if (addressEl) addressEl.textContent = '주소 조회 실패';
      if (popupRefs.fields.fullAddress) {
        popupRefs.fields.fullAddress.textContent = '주소 조회 실패';
      }
    });
}

async function fetchBuildingData(lon, lat, buildingId) {
  try {
    const eproData = await fetchDataFromCoords(lon, lat);

    let eproAge = '정보 없음';
    let eproPurpose = '정보 없음';
    let eproHeight = '정보 없음';
    let eproStructure = '정보 없음';
    let eproFloors = '정보 없음';

    if (eproData) {
      const age = eproData.BULD_SPANU_NUM ?? eproData.AVG_AGE;
      if (age != null && age !== '') eproAge = `${parseFloat(age).toFixed(1)} 년`;
      eproPurpose = eproData.BILD_PRPOS || eproData.BUILDING_TYPE || '정보 없음';
      eproHeight = eproData.BULD_HEIGHT ? `${eproData.BULD_HEIGHT} m` : '정보 없음';
      eproStructure = eproData.STRCT_TY_NM || '정보 없음';
      eproFloors = eproData.GRD_FLR_CNT ? `${eproData.GRD_FLR_CNT} 층` : '정보 없음';
    }

    const ageEl = $id('sidebar_age');
    const purposeEl = $id('sidebar_purpose');
    const heightEl = $id('sidebar_height');
    const structureEl = $id('sidebar_structure');
    const floorsEl = $id('sidebar_floors');

    if (ageEl) ageEl.textContent = eproAge;
    if (purposeEl) purposeEl.textContent = eproPurpose;
    if (heightEl) heightEl.textContent = eproHeight;
    if (structureEl) structureEl.textContent = eproStructure;
    if (floorsEl) floorsEl.textContent = eproFloors;

    updatePopupWithBuildingData({
      age: eproAge,
      purpose: eproPurpose,
      floors: eproFloors,
      structure: eproStructure
    });
  } catch (e) {
    console.error('fetchBuildingData error', e);
    updatePopupWithBuildingData({
      age: '정보 없음',
      purpose: '정보 없음',
      floors: '정보 없음',
      structure: '정보 없음'
    });
  }
}

async function fetchDataFromCoords(lon, lat) {
  try {
    const key = `${lon.toFixed(6)},${lat.toFixed(6)}`;
    if (_dataCache.has(key)) return _dataCache.get(key);

    const res = await fetch(`/api/get-data-from-coords?lon=${lon}&lat=${lat}`);
    if (!res.ok) return null;

    const json = await res.json();
    if (json.status === 'OK' && json.data) {
      _dataCache.set(key, json.data);
      return json.data;
    }
    return null;
  } catch (e) {
    return null;
  }
}

// --- 유틸리티 함수 ---
function debouncedHighlight(mapElement, attributes) {
  if (_highlightTimeout) clearTimeout(_highlightTimeout);
  _highlightTimeout = setTimeout(function() {
    try {
      if (mapElement && typeof mapElement.highlightFeatureByKey === 'function') {
        mapElement.highlightFeatureByKey(attributes);
      }
    } catch (e) {}
  }, _HIGHLIGHT_DELAY);
}

function formatCartographic(cartographic) {
  if (!cartographic) return '';
  var lon, lat, h;

  if (Array.isArray(cartographic)) {
    lon = cartographic[0];
    lat = cartographic[1];
    h = cartographic[2];
  } else if (typeof cartographic === 'object') {
    lon = cartographic.longitude || cartographic.lon || cartographic.x;
    lat = cartographic.latitude || cartographic.lat || cartographic.y;
    h = cartographic.height || cartographic.z;
  }

  function toRad(v) {
    if (v == null || !isFinite(v)) return null;
    return Math.abs(v) <= 2 * Math.PI ? (v * 180 / Math.PI).toFixed(6) : v.toFixed(6);
  }

  var lonD = toRad(lon);
  var latD = toRad(lat);
  if (!lonD || !latD) return '';
  return lonD + ', ' + latD + (h ? (' (h:' + h.toFixed(2) + ')') : '');
}

function extractLonLat(cartographic) {
  if (!cartographic) return null;
  var lon, lat, h;

  if (Array.isArray(cartographic)) {
    lon = cartographic[0];
    lat = cartographic[1];
    h = cartographic[2];
  } else if (typeof cartographic === 'object') {
    lon = cartographic.longitude || cartographic.lon || cartographic.x;
    lat = cartographic.latitude || cartographic.lat || cartographic.y;
    h = cartographic.height || cartographic.z;
  }

  if (lon == null || lat == null) return null;

  function toDeg(v) {
    if (v == null || !isFinite(v)) return null;
    return Math.abs(v) <= 2 * Math.PI ? v * 180 / Math.PI : v;
  }

  return {
    lon: toDeg(lon),
    lat: toDeg(lat),
    height: (h != null && isFinite(h)) ? Number(h) : null
  };
}

// --- 팝업 초기화 ---
function initMapPopup() {
  popupRefs.container = $id('mapPopup');
  popupRefs.closeBtn = $id('mapPopupClose');
  popupRefs.fields = {
    title: $id('popupTitle'),
    fullAddress: $id('popupFullAddress'),
    level1: $id('popupLevel1'),
    level2: $id('popupLevel2'),
    level3: $id('popupLevel3'),
    road: $id('popupRoad'),
    buildingNo: $id('popupBuildingNo'),
    detail: $id('popupDetail'),
    age: $id('popupAge'),
    purpose: $id('popupPurpose'),
    floors: $id('popupFloors'),
    structure: $id('popupStructure')
  };

  if (popupRefs.closeBtn) {
    popupRefs.closeBtn.addEventListener('click', hideMapPopup);
  }
}

function showMapPopup() {
  if (popupRefs.container) {
    popupRefs.container.classList.remove('hidden');
  }
}

function hideMapPopup() {
  if (popupRefs.container) {
    popupRefs.container.classList.add('hidden');
  }
}

function resetPopupDetails(buildingId) {
  if (!popupRefs.container) return;
  showMapPopup();
  const fields = popupRefs.fields;
  if (!fields) return;

  if (fields.title) {
    fields.title.textContent = buildingId ? `건물 정보 (${buildingId})` : '건물 정보';
  }
  if (fields.fullAddress) fields.fullAddress.textContent = '주소 조회 중...';
  if (fields.level1) fields.level1.textContent = '-';
  if (fields.level2) fields.level2.textContent = '-';
  if (fields.level3) fields.level3.textContent = '-';
  if (fields.road) fields.road.textContent = '-';
  if (fields.buildingNo) fields.buildingNo.textContent = '-';
  if (fields.detail) fields.detail.textContent = '-';
  if (fields.age) fields.age.textContent = '조회 중...';
  if (fields.purpose) fields.purpose.textContent = '조회 중...';
  if (fields.floors) fields.floors.textContent = '조회 중...';
  if (fields.structure) fields.structure.textContent = '조회 중...';
}

function buildPopupDetail(structure, firstResult) {
  const parts = [];

  function pushPart(value) {
    if (!value) return;
    const text = String(value).trim();
    if (!text) return;
    if (parts.indexOf(text) === -1) {
      parts.push(text);
    }
  }

  const firstStructure = firstResult?.structure || {};

  pushPart(structure.level4A || firstStructure.level4A);
  pushPart(structure.detail || firstStructure.detail);
  pushPart(firstResult?.detail);
  pushPart(structure.level6 || firstStructure.level6);
  pushPart(structure.buildingName || firstStructure.buildingName);

  return parts.join(' ');
}

function updatePopupWithAddress(response, fallbackRoadAddress) {
  if (!popupRefs.container) return;
  const fields = popupRefs.fields;
  if (!fields) return;

  const refined = response?.refined || {};
  const results = response?.result;
  const firstResult = Array.isArray(results) ? results[0] : results;
  const structure = refined.structure || firstResult?.structure || {};
  const fullText = refined.text || firstResult?.text || fallbackRoadAddress;
  const detailText = buildPopupDetail(structure, firstResult);

  if (fields.fullAddress) {
    fields.fullAddress.textContent = fullText || '주소 정보를 찾을 수 없습니다.';
  }
  if (fields.level1) fields.level1.textContent = structure.level1 || '-';
  if (fields.level2) fields.level2.textContent = structure.level2 || '-';
  if (fields.level3) fields.level3.textContent = structure.level3 || structure.level4A || '-';
  if (fields.road) fields.road.textContent = structure.level4L || structure.level4LC || '-';
  if (fields.buildingNo) fields.buildingNo.textContent = structure.level5 || '-';
  if (fields.detail) fields.detail.textContent = detailText || structure.detail || firstResult?.detail || '-';
}

function updatePopupWithBuildingData(buildingData) {
  if (!popupRefs.container) return;
  const fields = popupRefs.fields;
  if (!fields) return;

  if (fields.age) fields.age.textContent = buildingData.age;
  if (fields.purpose) fields.purpose.textContent = buildingData.purpose;
  if (fields.floors) fields.floors.textContent = buildingData.floors;
  if (fields.structure) fields.structure.textContent = buildingData.structure;
}

// --- 페이지 로드 ---
window.addEventListener('load', function() {
  console.log('페이지 로드 완료');

  initMapSidebar();
  initRegionSearch();
  initMapPopup();

  // VWorld API 대기
  var attempts = 0;
  var interval = setInterval(function() {
    attempts++;

    if (typeof vw !== 'undefined' && typeof vw.Map === 'function') {
      clearInterval(interval);
      console.log('VWorld API 로드 완료');

      setTimeout(function() {
        initializeMap();
      }, 500);
    } else if (attempts >= 50) {
      clearInterval(interval);
      console.error('VWorld API 로드 타임아웃');
      alert('지도를 로드할 수 없습니다. 페이지를 새로고침해주세요.');
    }
  }, 200);
});