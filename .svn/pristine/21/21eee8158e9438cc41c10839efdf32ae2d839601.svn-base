package com.daejeon.my.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.daejeon.my.vo.Location;

import java.util.List;

@Mapper
public interface LocationMapper {
    List<Location> findByMatchKey(@Param("matchKey") String matchKey);
}
