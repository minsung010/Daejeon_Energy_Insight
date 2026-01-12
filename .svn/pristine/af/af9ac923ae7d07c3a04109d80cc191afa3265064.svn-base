package com.daejeon.my.notice.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class NoticeController {

    @GetMapping("/notice")
    public String notice(Model model) {
  	  model.addAttribute("activeMenu", "notice");
        return "Epro_notice";
    }
    
    @GetMapping("/first-notice")
    public String firstNotice() {
        return "Epro_firstnotice";
    }

}
