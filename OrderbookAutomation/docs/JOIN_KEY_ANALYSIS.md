# JOIN_KEY_ANALYSIS

Generated from Phase 1 header discovery across loaded workbooks.

| Candidate Key | Header Hints | Workbook Coverage | Worksheet Coverage | Confidence % | Locations |
| --- | --- | --- | --- | --- | --- |
| NDC | NDC, NDC code, NDC Code | 6 | 6 | 75.0 | 07-30_inv.xlsx::Sheet1, Awards.xlsx::Sheet1, CIP.xlsx::Sheet1, MOQ.xlsx::Sheet1, Strend.xlsx::Sheet1, raw_OB.xlsx::UOB |
| Customer | Customer, Sold-to party Name, PH_SOLDTO_NAME | 5 | 5 | 62.5 | Awards.xlsx::Sheet1, Buying_groups.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1, Strend.xlsx::Sheet1, raw_OB.xlsx::UOB |
| Sold-to Party | Sold-to party, Sold to party, PH_SOLDTO_NAME | 3 | 3 | 37.5 | Awards.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1, raw_OB.xlsx::UOB |
| Lookup | Lookup, x | 3 | 3 | 37.5 | Awards.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1, Strend.xlsx::Sheet1 |
| SKU | SKU | 2 | 2 | 25.0 | 07-30_inv.xlsx::Sheet1, Open_Order_Summary.xlsx::Sheet1 |
| Sales Order | Sales Order No., SO#, Sales Order Qty | 2 | 2 | 25.0 | Open_Order_Summary.xlsx::Sheet1, raw_OB.xlsx::UOB |
| Material Number | HANA Material, Matl._x000d_
Code, Material Number | 1 | 1 | 12.5 | MOQ.xlsx::Sheet1 |