package com.daejeon.my.dashboard.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
public class DashboardController {

	@GetMapping({"/", "/dashboard"})
	public String dashboard(Model model) {
	  model.addAttribute("activeMenu", "dashboard");
	  return "Epro_dashboard";
	}

}
