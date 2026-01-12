package com.daejeon.my.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;
import java.util.Map;

@Mapper
public interface EnergyUsageMapper {

    /** 1. (Viz 1) '내 주택' 연도별 평균 TOE/AREA */
    List<Map<String, Object>> findMyHouseEnergyData(@Param("matchKey") String matchKey);

    /** 2. (Viz 2) '인근 주택' (키 목록)의 에너지 평균 */
    Map<String, Object> findNearbyEnergyAverage(@Param("matchKeys") List<String> matchKeys);

    /** 3. (Viz 3) '지역' (구)의 에너지 평균 */
    Map<String, Object> findRegionEnergyAverage(@Param("guName") String guName,
                                                @Param("purposeEquals") String purposeEquals,
                                                @Param("purposeLike") String purposeLike);

    /** 4. (Viz 2) '인근 주택' 연도별 에너지 평균 */
    List<Map<String, Object>> findNearbyEnergySeries(@Param("matchKeys") List<String> matchKeys);

    /** 5. (Viz 3) '지역' 연도별 에너지 평균 */
    List<Map<String, Object>> findRegionEnergySeries(@Param("guName") String guName,
                                                     @Param("purposeEquals") String purposeEquals,
                                                     @Param("purposeLike") String purposeLike);
}