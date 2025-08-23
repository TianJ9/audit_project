```sql
SELECT engineering_settlement_date
FROM   (
           SELECT proj.pspid AS prj_code
                  ,proj.post1 AS prj_name
                  ,prps.stufe AS prj_level
                  ,substr(prps.posid, 1, 14) single_prj_code_14
                  ,prps.posid AS single_prj_code
                  ,prps.post1 AS single_prj_name
                  ,prps.usr08 AS operation_start_date
                  ,bkpf.bldat AS capitial_date
                  ,prps.ZGCJSRQ AS engineering_settlement_date
                  ,ROW_NUMBER() OVER(PARTITION BY proj.pspid, proj.post1, prps.stufe, substr(prps.posid, 1, 14), prps.posid, prps.post1, prps.usr08 ORDER BY prps.ZGCJSRQ) row_index
           FROM   PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
           LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
           ON     PROJ.PSPNR = prps.PSPHI
           AND    LENGTH(TRIM(PRPS.PSPNR)) > 0
           AND    prps.stufe IN (1, 2)
           AND    PRPS.mandt = '880'
           AND    PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')
           LEFT JOIN (
                         SELECT prj_code
                                ,COUNT(DISTINCT single_prj_code_14) AS NUM
                         FROM   (
                                    SELECT DISTINCT proj.pspid AS prj_code
                                           ,substr(prps.posid, 1, 14) single_prj_code_14
                                    FROM   PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
                                    LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
                                    ON     PROJ.PSPNR = prps.PSPHI
                                    AND    LENGTH(TRIM(PRPS.PSPNR)) > 0
                                    AND    prps.stufe IN (1, 2)
                                    AND    PRPS.mandt = '880'
                                    AND    PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')
                                    WHERE  proj.mandt = '880'
                                    AND    proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')
                                )
                         GROUP BY prj_code
                     ) mid_tmp_filter_table
           ON     mid_tmp_filter_table.prj_code = proj.pspid
           LEFT JOIN (
                         SELECT gjahr
                                ,belnr
                                ,bukrs
                                ,mandt
                                ,sgtxt
                                ,hkont
                         FROM   pro_dwh_erp_prd.ods_erp_zltp_erp_bseg
                     ) bseg
           ON     substr(bseg.sgtxt, 5, 14) = substr(prps.posid, 1, 14)
           AND    bseg.mandt = '880'
           AND    substr(bseg.hkont, 1, 4) = '1601'
           LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_bkpf bkpf
           ON     bseg.bukrs = bkpf.bukrs
           AND    bseg.belnr = bkpf.belnr
           AND    bseg.gjahr = bkpf.gjahr
           AND    bkpf.ds = max_pt('pro_dwh_erp_prd.ods_erp_p00_sapsr3_bkpf')
           WHERE  proj.mandt = '880'
           AND    proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')
           AND    CASE WHEN mid_tmp_filter_table.NUM = 1 THEN prps.stufe = 1 ELSE prps.stufe = 2 END
           AND    proj.pspid IN ('18138721004F', '18138721004B', '18138721000U')
       )
WHERE  row_index = 1
```