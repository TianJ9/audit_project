```sql
SELECT  ZGCJSRQ AS 工程结算日期
FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
ON      PROJ.PSPNR = prps.PSPHI
AND     LENGTH(TRIM(PRPS.PSPNR)) > 0
AND     PRPS.mandt = '880'
AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')
WHERE   proj.mandt = '880'
AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')
AND     proj.pspid in ('18138721004F', '18138721004B', '18138721000U');
```