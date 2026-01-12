package com.daejeon.my.controller;

import com.daejeon.my.dao.LocationMapper;
import com.daejeon.my.vo.Location;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/locations")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class LocationApiController {

    private final LocationMapper locationMapper;

    @GetMapping
    public List<Location> getByMatchKey(@RequestParam("matchKey") String matchKey) {
        return locationMapper.findByMatchKey(matchKey);
    }
}
