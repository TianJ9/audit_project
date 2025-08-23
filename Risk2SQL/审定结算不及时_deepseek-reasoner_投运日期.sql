```sql
SELECT  *
FROM    (
            SELECT  proj.pspid AS project_code    -- 项目编码
                    ,prps.posid AS single_project_code    -- 单体工程编码
                    ,prps.usr08 AS operation_date    -- 投运日期
                    ,ROW_NUMBER() OVER(PARTITION BY proj.pspid, prps.posid ORDER BY prps.usr08 DESC) row_index
            FROM    PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ proj
            LEFT JOIN pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps PRPS
            ON      PROJ.PSPNR = prps.PSPHI
            AND     LENGTH(TRIM(PRPS.PSPNR)) > 0
            AND     prps.stufe IN (1, 2)
            AND     PRPS.mandt = '880'
            AND     PRPS.ds = MAX_PT('pro_dwh_erp_prd.ods_erp_p00_sapsr3_prps')
            WHERE   proj.mandt = '880'
            AND     proj.ds = MAX_PT('PRO_DWH_ERP_PRD.ods_erp_p00_sapsr3_PROJ')
            AND     proj.pspid in 
            ('18138721004F', '18138721004B', '18138721000U')  
        ) 
WHERE   row_index = 1
```