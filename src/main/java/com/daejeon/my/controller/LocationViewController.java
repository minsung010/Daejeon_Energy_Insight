package com.daejeon.my.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class LocationViewController {

    @GetMapping("/pppddldl")
    public String searchPage() {
        return "location-search";
    }
}
