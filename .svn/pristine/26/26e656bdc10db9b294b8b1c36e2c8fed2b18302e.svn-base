package com.daejeon.my.map.service;

import com.daejeon.my.dao.BuildingMasterMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class BuildingDataService {

    private final BuildingMasterMapper buildingMasterMapper;

    @Value("${daejeon.nearest.maxDistanceMeters:20}")
    private double maxDistanceMeters;

    @Value("${daejeon.nearest.candidateLimit:50}")
    private int candidateLimit;

    public BuildingDataService(BuildingMasterMapper buildingMasterMapper) {
        this.buildingMasterMapper = buildingMasterMapper;
    }

    public Map<String,Object> findNearest(double lon, double lat) {
        double latRad = Math.toRadians(lat);
        double deltaLatDeg = metersToLatDegrees(maxDistanceMeters);
        double deltaLonDeg = metersToLonDegrees(maxDistanceMeters, latRad);

        double minLat = lat - deltaLatDeg;
        double maxLat = lat + deltaLatDeg;
        double minLon = lon - deltaLonDeg;
        double maxLon = lon + deltaLonDeg;

        // [⭐️⭐️⭐️ 핵심 수정 ⭐️⭐️⭐️]
        // BuildingMasterMapper.java 인터페이스에 정의된 순서와
        // (minLat, maxLat, minLon, maxLon, targetLat, targetLon, limit)
        // 여기의 호출 순서를 정확히 일치시킵니다.
        List<Map<String, Object>> candidates = buildingMasterMapper.findCandidatesByBoundingBox(
            minLat, maxLat, minLon, maxLon, lat, lon, candidateLimit
        );
        // [⭐️⭐️⭐️ 수정 완료 ⭐️⭐️⭐️]
        

        if (candidates == null || candidates.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND,
                    String.format("%.1fm 반경 내 데이터 없음", maxDistanceMeters));
        }

        Map<String, Object> best = null;
        double minDistance = Double.MAX_VALUE;

        // (이하 Java 로직은 하버사인 거리를 계산하는 효율적인 로직이므로 그대로 둡니다)
        for (Map<String, Object> candidate : candidates) {
            BigDecimal candLat = asBigDecimal(candidate.get("LATITUDE"));
            BigDecimal candLon = asBigDecimal(candidate.get("LONGITUDE"));
            if (candLat == null || candLon == null) continue;

            double distance = haversineMeters(lat, lon, candLat.doubleValue(), candLon.doubleValue());
            if (distance < minDistance) {
                minDistance = distance;
                best = candidate;
            }
        }

        if (best == null || minDistance > maxDistanceMeters) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND,
                    String.format("%.1fm 반경 내 데이터 없음", maxDistanceMeters));
        }

        Map<String,Object> res = new LinkedHashMap<>();
        res.put("status", "OK");
        res.put("distance_m", Math.round(minDistance * 100.0) / 100.0);
        res.put("data", best);
        return res;
    }

    // (asBigDecimal, metersToLatDegrees 등 private 헬퍼 함수들은 변경 없이 그대로 둡니다)
    private static BigDecimal asBigDecimal(Object value) {
        if (value instanceof BigDecimal bd) { return bd; }
        if (value instanceof Number number) { return BigDecimal.valueOf(number.doubleValue()); }
        if (value instanceof String str && !str.isBlank()) {
            try { return new BigDecimal(str); } catch (NumberFormatException ignore) {}
        }
        return null;
    }
    private static double metersToLatDegrees(double meters) {
        return meters / 111_320d;
    }
    private static double metersToLonDegrees(double meters, double latRad) {
        double denom = Math.cos(latRad) * 111_320d;
        if (denom == 0) return meters / 111_320d;
        return meters / denom;
    }
    private static double haversineMeters(double lat1, double lon1, double lat2, double lon2) {
        double R = 6371000.0;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat/2)*Math.sin(dLat/2)
                + Math.cos(Math.toRadians(lat1))*Math.cos(Math.toRadians(lat2))
                * Math.sin(dLon/2)*Math.sin(dLon/2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
}