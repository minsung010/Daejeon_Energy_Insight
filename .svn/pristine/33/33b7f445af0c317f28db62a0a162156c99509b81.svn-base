package com.daejeon.my.map.controller;

import com.daejeon.my.map.service.MapDataService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api") 
public class MapDataController {

    @Autowired
    private MapDataService mapDataService; // (방금 만든 새 Service)

    /**
     * ECharts 그래프 3종 세트 데이터를 반환
     */
    @GetMapping("/dashboard-data")
    public ResponseEntity<Map<String, Object>> getDashboardData(
            @RequestParam("lon") double lon,
            @RequestParam("lat") double lat,
            @RequestParam(value = "gu", required = false) String gu,
            @RequestParam(value = "roadAddress", required = false) String roadAddress) {
        
        try {
            Map<String, Object> data = mapDataService.getDashboardData(lon, lat, gu, roadAddress);
            if (data.containsKey("error")) {
                return ResponseEntity.status(404).body(data);
            }
            return ResponseEntity.ok(data);
            
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body(Map.of("error", e.getMessage()));
        }
    }
}