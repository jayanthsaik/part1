# JOIN_KEY_ANALYSIS

Generated from Phase 1 header discovery across loaded workbooks.

| Candidate Key | Header Hints | Workbook Coverage | Worksheet Coverage | Confidence % | Locations |
| --- | --- | --- | --- | --- | --- |
| NDC | NDC, NDC code, NDC Code | 7 | 7 | 77.78 | 07-30_inv.xlsx::Sheet1, Awards.xlsx::Sheet1, CIP.xlsx::Sheet1, Mat_Desc,_MOQ_,_Material_#.xlsx::Sheet1, Strend.xlsx::Sheet1, raw_OB.xlsx::UOB, sales_summ.xlsx::Sheet1 |
| Customer | Customer, Sold-to party Name, PH_SOLDTO_NAME | 6 | 6 | 66.67 | Awards.xlsx::Sheet1, Buying_groups.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1, Strend.xlsx::Sheet1, raw_OB.xlsx::UOB, sales_summ.xlsx::Sheet1 |
| Sold-to Party | Sold-to party, Sold to party, PH_SOLDTO_NAME | 4 | 4 | 44.44 | Awards.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1, raw_OB.xlsx::UOB, sales_summ.xlsx::Sheet1 |
| Lookup | Lookup, x | 4 | 4 | 44.44 | Awards.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1, Strend.xlsx::Sheet1, sales_summ.xlsx::Sheet1 |
| Sales Order | Sales Order No., SO#, Sales Order Qty | 3 | 3 | 33.33 | Open_Order_Summary.xlsx::Sheet1, raw_OB.xlsx::UOB, sales_summ.xlsx::Sheet1 |
| Material Number | HANA Material, Matl._x000d_
Code, Material Number | 2 | 2 | 22.22 | Mat_Desc,_MOQ_,_Material_#.xlsx::Sheet1, sales_summ.xlsx::Sheet1 |
| SKU | SKU | 2 | 2 | 22.22 | 07-30_inv.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1 |