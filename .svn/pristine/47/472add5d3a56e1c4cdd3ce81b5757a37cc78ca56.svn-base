package com.daejeon.my.graph.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class GraphController {

    @GetMapping("/graph")
    public String graph(Model model) {
    	model.addAttribute("activeMenu", "graph");
        // templates/Epro_graph.html
        return "Epro_graph";
    }
}
