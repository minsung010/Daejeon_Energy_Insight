package com.daejeon.my.map.controller;

import com.daejeon.my.map.service.BuildingDataService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class NearestController {

  private final BuildingDataService service;
  public NearestController(BuildingDataService service) { this.service = service; }

  @GetMapping("/get-data-from-coords")
  public ResponseEntity<Map<String,Object>> getDataFromCoords(
      @RequestParam double lon, @RequestParam double lat) {
    return ResponseEntity.ok(service.findNearest(lon, lat));
  }
}
