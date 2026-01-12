package com.daejeon.my.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

@Mapper
public interface BuildingMasterMapper {

    List<Map<String, Object>> findCandidatesByBoundingBox(
        @Param("minLat") double minLat,
        @Param("maxLat") double maxLat,
        @Param("minLon") double minLon,
        @Param("maxLon") double maxLon,
        @Param("targetLat") double targetLat,
        @Param("targetLon") double targetLon,
        @Param("limit") int limit
    );
}
