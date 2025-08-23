```sql
SELECT 投运日期
FROM   (
           SELECT prps.usr08 AS投运日期,
                  ROW_NUMBER() OVER(PARTITION BY proj.pspid, proj.post1, prps.stufe, substr(prps.posid, 1, 14), prps.posid, prps.post1 ORDER BY prps.usr08 ASC) row_index
           FROM   PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
           LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
           ON     PROJ.PSPNR = prps.PSPHI
           AND    LENGTH(TRIM(PRPS.PSPNR)) > 0
           AND    prps.stufe IN (1, 2)
           AND    PRPS.mandt = '880'
           AND    PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')
           WHERE  proj.mandt = '880'
           AND    proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ'))
WHERE  row_index = 1
```