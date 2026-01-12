package com.daejeon.my.map.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/map")   
public class ViewController {

  @Value("${daejeon.vworld.key}")
  private String vworldKey;

  @GetMapping
  public String index(Model model) {
    model.addAttribute("vworldKey", vworldKey);
    model.addAttribute("activeMenu", "map");   // ★ 하이라이트용
    return "Epro_map"; 
  }
}
