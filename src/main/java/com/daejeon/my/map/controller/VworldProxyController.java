package com.daejeon.my.map.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class VworldProxyController {

  private final RestTemplate rt = new RestTemplate();

  @Value("${daejeon.vworld.key}")
  private String apiKey;

  private static final String ADDR_URL = "https://api.vworld.kr/req/address";
  private static final String SEARCH_URL = "https://api.vworld.kr/req/search";

  // 좌표 -> 도로명 주소
  @GetMapping("/get_address")
  public ResponseEntity<String> getAddress(@RequestParam double lon, @RequestParam double lat) {
    String url = ADDR_URL + "?service=address&request=getaddress&crs=epsg:4326"
        + "&point=" + lon + "," + lat
        + "&format=json&type=road&key=" + enc(apiKey);
    return rt.getForEntity(URI.create(url), String.class);
  }

  // 주소 -> 좌표 (도로명 우선, 실패 시 지번)
  @GetMapping("/geocode")
  public ResponseEntity<String> geocode(@RequestParam String query) {
    String common = "&service=address&request=getcoord&version=2.0&crs=epsg:4326"
        + "&refine=true&simple=false&format=json&address=" + enc(query)
        + "&key=" + enc(apiKey);

    ResponseEntity<String> road = rt.getForEntity(URI.create(ADDR_URL + "?type=road" + common), String.class);
    if (road.getStatusCode().is2xxSuccessful() && containsOk(road.getBody())) {
      return road;
    }
    return rt.getForEntity(URI.create(ADDR_URL + "?type=parcel" + common), String.class);
  }

  // 검색 프록시 (CORS 우회)
  @GetMapping("/search_address")
  public ResponseEntity<String> searchAddress(@RequestParam Map<String,String> params) {
    StringBuilder sb = new StringBuilder(SEARCH_URL)
        .append("?service=search&request=search&version=2.0&format=json&errorformat=json&crs=EPSG:4326")
        .append("&key=").append(enc(apiKey));

    params.forEach((k,v) -> {
      if (!"key".equalsIgnoreCase(k) && v != null && !v.isBlank()) {
        sb.append("&").append(enc(k)).append("=").append(enc(v));
      }
    });

    return rt.getForEntity(URI.create(sb.toString()), String.class);
  }

  private static boolean containsOk(String body) {
    return body != null && body.contains("\"status\":\"OK\"");
  }
  private static String enc(String s) {
    return URLEncoder.encode(s, StandardCharsets.UTF_8);
  }
}
