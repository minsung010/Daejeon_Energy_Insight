package com.daejeon.my.map.service;

import com.daejeon.my.dao.BuildingMasterMapper;
import com.daejeon.my.dao.EnergyUsageMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class MapDataService {

    private static final Logger log = LoggerFactory.getLogger(MapDataService.class);

    @Autowired
    private BuildingMasterMapper buildingMapper; 

    @Autowired
    private EnergyUsageMapper energyMapper; 
    
    // (기존 BuildingDataService의 Bounding Box 계산 로직 재사용)
    private Map<String, Double> getBoundingBox(double lon, double lat, double radiusM) {
        double latDegree = 110941.0; 
        double lonDegree = 88716.0; 
        double radiusLat = radiusM / latDegree;
        double radiusLon = radiusM / lonDegree;
        
        Map<String, Double> bounds = new HashMap<>();
        bounds.put("minLat", lat - radiusLat);
        bounds.put("maxLat", lat + radiusLat);
        bounds.put("minLon", lon - radiusLon);
        bounds.put("maxLon", lon + radiusLon);
        return bounds;
    }
    
    // (노후도 4단계 분류 로직)
    private String getAgeCategory(Object ageObj) {
        if (ageObj == null) return "정보 없음";
        double ageNum = 0.0;
        
        if (ageObj instanceof BigDecimal bd) {
             ageNum = bd.doubleValue();
        } else if (ageObj instanceof Number num) {
             ageNum = num.doubleValue();
        } else {
             return "정보 없음";
        }

        if (ageNum <= 9) return "0~9년";
        if (ageNum <= 20) return "10~20년"; // (JS와 동일한 20년 기준)
        if (ageNum <= 30) return "20~30년"; // (JS와 동일한 30년 기준)
        return "30년이상";
    }

    private String normalizeText(String text) {
        if (text == null) return "";
        return text.replaceAll("[^\\p{L}\\p{N}]", "").toUpperCase();
    }

    private Map<String, Object> selectPrimaryCandidate(List<Map<String, Object>> candidates, String gu, String roadAddress) {
        if (candidates == null || candidates.isEmpty()) return null;

        if (roadAddress != null && !roadAddress.isBlank()) {
            String normalizedRoad = normalizeText(roadAddress);
            if (!normalizedRoad.isEmpty()) {
                for (Map<String, Object> candidate : candidates) {
                    Object locationObj = candidate.get("LOCATION");
                    if (locationObj != null) {
                        String normalizedLocation = normalizeText(locationObj.toString());
                        if (!normalizedLocation.isEmpty()) {
                            if (normalizedLocation.contains(normalizedRoad) || normalizedRoad.contains(normalizedLocation)) {
                                return candidate;
                            }
                        }
                    }
                }
            }
        }

        if (gu != null && !gu.isBlank()) {
            String normalizedGu = gu.replaceAll("\\s+", "").toUpperCase();
            if (!normalizedGu.isEmpty()) {
                for (Map<String, Object> candidate : candidates) {
                    Object guNameObj = candidate.get("GU_NAME");
                    if (guNameObj != null) {
                        String normalizedCandidateGu = guNameObj.toString().replaceAll("\\s+", "").toUpperCase();
                        if (normalizedGu.equals(normalizedCandidateGu)) {
                            return candidate;
                        }
                    }
                }
            }
        }

        return candidates.get(0);
    }

    private Object firstPresent(Map<String, Object> source, String... keys) {
        if (source == null || keys == null) return null;
        for (String key : keys) {
            if (key == null) continue;
            if (source.containsKey(key) && source.get(key) != null) {
                return source.get(key);
            }
            String upper = key.toUpperCase();
            if (source.containsKey(upper) && source.get(upper) != null) {
                return source.get(upper);
            }
            String lower = key.toLowerCase();
            if (source.containsKey(lower) && source.get(lower) != null) {
                return source.get(lower);
            }
        }
        return null;
    }

    private List<Map<String, Object>> normalizeEnergyRows(List<Map<String, Object>> rawRows) {
        if (rawRows == null) return List.of();
        return rawRows.stream().map(row -> {
            Map<String, Object> normalized = new HashMap<>();
            normalized.put("year", firstPresent(row, "year"));
            normalized.put("use_total", firstPresent(row, "use_total"));
            normalized.put("use_electric", firstPresent(row, "use_electric"));
            normalized.put("use_gas", firstPresent(row, "use_gas"));
            normalized.put("toe_per_area", firstPresent(row, "toe_per_area"));
            return normalized;
        }).collect(Collectors.toList());
    }

    /**
     * 지도를 클릭했을 때 그래프 3종 세트 데이터를 반환
     */
    public Map<String, Object> getDashboardData(double lon, double lat, String gu, String roadAddress) {

        if (log.isDebugEnabled()) {
            log.debug("[dashboard-data] request lon={}, lat={}, gu={}, roadAddress={}", lon, lat, gu, roadAddress);
        }

        Map<String, Object> result = new HashMap<>();
        Map<String, Object> myHouseResult = new HashMap<>();
        Map<String, Object> nearbyResult = new HashMap<>();
        Map<String, Object> regionResult = new HashMap<>();
        
        // --- 1. '내 주택' 및 '인근 주택' 후보 찾기 (500m 반경) ---
        Map<String, Double> bounds = getBoundingBox(lon, lat, 500.0);
        
        // (BuildingDataService와 동일하게, Mapper 호출 순서 준수)
        List<Map<String, Object>> candidates = buildingMapper.findCandidatesByBoundingBox(
            bounds.get("minLat"), bounds.get("maxLat"), 
            bounds.get("minLon"), bounds.get("maxLon"), 
            lat, lon, 
            100 // (인근 100개 건물로 제한)
        );

        if (log.isDebugEnabled()) {
            log.debug("[dashboard-data] candidate count={} (500m radius)",
                    candidates != null ? candidates.size() : 0);
        }

        if (candidates == null || candidates.isEmpty()) {
            result.put("error", "주변 500m 내에 건물이 없습니다.");
            return result;
        }

        // --- 2. '내 주택' (Viz 1) ---
        Map<String, Object> myHouse = selectPrimaryCandidate(candidates, gu, roadAddress);
        if (myHouse == null) {
            myHouse = candidates.get(0);
        }
        String myHouseMatchKey = (String) myHouse.get("MATCH_KEY");
        if (log.isDebugEnabled()) {
            log.debug("[dashboard-data] selected matchKey={} (gu={}, roadHint={})",
                    myHouseMatchKey, myHouse.get("GU_NAME"), myHouse.get("LOCATION"));
        }
        String myHouseGuName = (String) myHouse.get("GU_NAME");
        String myHouseBildPrpos = (String) myHouse.get("BILD_PRPOS");
        String myHouseAgeCategory = getAgeCategory(myHouse.get("BULD_SPANU_NUM"));
        
        myHouseResult.put("match_key", myHouseMatchKey);
        myHouseResult.put("age", myHouse.get("BULD_SPANU_NUM"));
        myHouseResult.put("purpose", myHouseBildPrpos);
        myHouseResult.put("ageCategory", myHouseAgeCategory); // (JS에서 사용)
        
        List<Map<String, Object>> myHouseEnergy = energyMapper.findMyHouseEnergyData(myHouseMatchKey);
        myHouseResult.put("energyData", normalizeEnergyRows(myHouseEnergy));

        if (log.isDebugEnabled()) {
            log.debug("[dashboard-data] energy rows for {} = {}", myHouseMatchKey,
                    myHouseEnergy != null ? myHouseEnergy.size() : 0);
            if (myHouseEnergy != null && !myHouseEnergy.isEmpty()) {
                log.debug("[dashboard-data] sample energy row: {}", myHouseEnergy.get(0));
            }
        }

        result.put("myHouse", myHouseResult);

        // --- 3. '인근 주택' (Viz 2) ---
        List<String> nearbyMatchKeys = candidates.stream()
                                    .map(c -> (String) c.get("MATCH_KEY"))
                                    .collect(Collectors.toList());

        // (Mapper를 수정하여 '유형'과 '노후도'로 필터링)
        // (EnergyUsageMapper.xml도 이와 맞게 수정해야 함)
        Map<String, Object> nearbyAverages = energyMapper.findNearbyEnergyAverage(nearbyMatchKeys);
        List<Map<String, Object>> nearbySeriesRows = energyMapper.findNearbyEnergySeries(nearbyMatchKeys);
        if (nearbyAverages != null) {
            nearbyResult.put("avg_toe", firstPresent(nearbyAverages, "avg_toe"));
            nearbyResult.put("avg_total", firstPresent(nearbyAverages, "avg_total"));
            nearbyResult.put("avg_electric", firstPresent(nearbyAverages, "avg_electric"));
            nearbyResult.put("avg_gas", firstPresent(nearbyAverages, "avg_gas"));
        } else {
            nearbyResult.put("avg_toe", null);
            nearbyResult.put("avg_total", null);
            nearbyResult.put("avg_electric", null);
            nearbyResult.put("avg_gas", null);
        }
        nearbyResult.put("series", normalizeEnergyRows(nearbySeriesRows));
        nearbyResult.put("count", nearbyMatchKeys.size());
        result.put("nearby", nearbyResult);

        if (log.isDebugEnabled()) {
            log.debug("[dashboard-data] nearby averages: {}", nearbyResult);
        }

        // --- 4. '지역' (Viz 3) ---
        String resolvedGu = (myHouseGuName != null && !myHouseGuName.isBlank())
                ? myHouseGuName
                : (gu != null ? gu : null);
        String purposeExact = null;
        String purposeLike = null;
        if (myHouseBildPrpos != null) {
            String trimmed = myHouseBildPrpos.trim();
            if (!trimmed.isEmpty()) {
                purposeExact = trimmed;
                purposeLike = "%" + trimmed + "%";
            }
        }

        Map<String, Object> regionAverages = resolvedGu != null
                ? energyMapper.findRegionEnergyAverage(resolvedGu, purposeExact, purposeLike)
                : null;
        List<Map<String, Object>> regionSeriesRows = resolvedGu != null
                ? energyMapper.findRegionEnergySeries(resolvedGu, purposeExact, purposeLike)
                : List.of();
        regionResult.put("region_name", resolvedGu);
        regionResult.put("purpose_filter", purposeExact);
        if (regionAverages != null) {
            regionResult.put("avg_toe", firstPresent(regionAverages, "avg_toe"));
            regionResult.put("avg_total", firstPresent(regionAverages, "avg_total"));
            regionResult.put("avg_electric", firstPresent(regionAverages, "avg_electric"));
            regionResult.put("avg_gas", firstPresent(regionAverages, "avg_gas"));
        } else {
            regionResult.put("avg_toe", null);
            regionResult.put("avg_total", null);
            regionResult.put("avg_electric", null);
            regionResult.put("avg_gas", null);
        }
        regionResult.put("series", normalizeEnergyRows(regionSeriesRows));
        result.put("region", regionResult);

        if (log.isDebugEnabled()) {
            log.debug("[dashboard-data] region averages: {}", regionResult);
        }

        return result;
    }
}