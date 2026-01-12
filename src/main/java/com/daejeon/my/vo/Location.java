package com.daejeon.my.vo;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class Location {
	//테이블 명 ENERGY_USING
	private Long signguOid;            // SIGNGU_OID   	 	 시군구고유번호
    private String bdnbr;              // BDNBR 		 	 건물번호
    private Long innb;                 // INNB			 	 고유번호
    private String legaldong;          // LEGALDONG		 	 법정동명
    private String lnno;               // LNNO			 	 지번
    private String spcgClsf;           // SPCG_CLSF		 	 공간분류코드
    private String bildPrpos;          // BILD_PRPOS	 	 건물용도
    private BigDecimal bildArea;       // BILD_AREA		 	 건축면적
    private String useAprvY;           // USE_APRV_Y	 	 사용승인일
    private BigDecimal grfa;           // GRFA			 	 연면적
    private BigDecimal siar;           // SIAR			 	 대지면적
    private BigDecimal hght;           // HGHT			 	 높이
    private BigDecimal btlr;           // BTLR				 건폐율
    private BigDecimal fart;           // FART			 	 용적률
    private Long bildId;               // BILD_ID		 	 건물ID
    private String vltnBild;           // VLTN_BILD		 	 위반건축물여부
    private String dataStndt;          // DATA_STNDT		 데이터 기준일
    private BigDecimal buldSpanu;      // BULD_SPANU		 노후도
    private BigDecimal buldSpanuNum;   // BULD_SPANU_NUM	 노후도
    private String guName;             // GU_NAME			 행정구
    private BigDecimal latitude;       // LATITUDE (15,8)	 위도
    private BigDecimal longitude;      // LONGITUDE (15,8)   경도
    private String legaldongKey;       // LEGALDONG_KEY		 주소(키)
    private String matchKey;           // MATCH_KEY			 상세주소(키)
    private String location;           // LOCATION			 대지위치
    private String mainaddress;        // MAINADDRESS		 번
    private String subaddress;         // SUBADDRESS		 지
    private String useDate;            // USE_DATE			 사용년월
    private BigDecimal useElectric;    // USE_ELECTRIC		 전기 사용량
    private BigDecimal useGas;         // USE_GAS			 가스 사용량
    private BigDecimal useTotal;       // USE_TOTAL			 총합 사용량
    private BigDecimal toeElectric;    // TOE_ELECTRIC		 전기 TOE
    private BigDecimal toeGas;         // TOE_GAS			 가스 TOE
    private BigDecimal toeTotal;       // TOE_TOTAL			 총합 TOE
    private BigDecimal carbonElectric; // CARBON_ELECTRIC	 전기 탄소배출량
    private BigDecimal carbonGas;      // CARBON_GAS		 가스 탄소배출량
    private BigDecimal carbonTotal;    // CARBON_TOTAL		 총합 탄소배출량
}
