# DATA_DICTIONARY

Generated from Phase 1 workbook ingestion.

## 07-30_inv.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 07-30_inv.xlsx | Sheet1 | NDC | int64 | 64380016101 | 0 | 4 | NDC | Potential National Drug Code field |
| 07-30_inv.xlsx | Sheet1 | SKU | str | 64380-161-01 | 0 | 4 | SKU | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | Description | str | Valganciclovir Tablets 450mg 60ct | 0 | 4 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | Lot | str | 7262830A | 0 | 16 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | Expiration Date | int64 | 46507 | 0 | 9 | UNKNOWN | Potential date field |
| 07-30_inv.xlsx | Sheet1 | Hold Codes | str | SD,HD | 7 | 5 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | Product Status | str |  | 0 | 1 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | Actual Quantity | int64 | 24 | 0 | 12 | UNKNOWN | Potential quantity field |
| 07-30_inv.xlsx | Sheet1 | Allocated Quantity | int64 | 0 | 0 | 1 | UNKNOWN | Potential quantity field |
| 07-30_inv.xlsx | Sheet1 | Inventory | int64 | 24 | 0 | 12 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | On Hand Damaged | int64 | 0 | 0 | 1 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | On Hand Hold | int64 | 24 | 0 | 7 | UNKNOWN | UNKNOWN |
| 07-30_inv.xlsx | Sheet1 | On Hand Misc | int64 | 0 | 0 | 1 | UNKNOWN | UNKNOWN |

## Awards.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Awards.xlsx | Sheet1 | Lookup | str | 64380072701CAH GLOBAL CONTRACTING COMPANY LTD | 0 | 129 | Lookup | Potential composite lookup key |
| Awards.xlsx | Sheet1 | NDC | int64 | 64380072701 | 0 | 3 | NDC | Potential National Drug Code field |
| Awards.xlsx | Sheet1 | Product | str | Gaba Tabs | 0 | 2 | UNKNOWN | UNKNOWN |
| Awards.xlsx | Sheet1 | Description | str | Gabapentin Tablets 600Mg 100Ct | 0 | 2 | UNKNOWN | UNKNOWN |
| Awards.xlsx | Sheet1 | Customer | str | Cardinal Health | 0 | 16 | Customer | Potential customer/account field |
| Awards.xlsx | Sheet1 | Award Type | str | Backup | 11 | 5 | UNKNOWN | UNKNOWN |
| Awards.xlsx | Sheet1 | Sold to party | str | CAH GLOBAL CONTRACTING COMPANY LTD | 0 | 80 | Sold-to Party | Potential customer/account field |

## Buying_groups.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Buying_groups.xlsx | Sheet1 | Customer | str | American Health Packaging | 0 | 13 | Customer | Potential customer/account field |
| Buying_groups.xlsx | Sheet1 | Customer buying group | str | AHP | 0 | 4 | UNKNOWN | Potential customer/account field |

## CIP.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CIP.xlsx | Sheet1 | NDC | int64 | 64380016001 | 0 | 10 | NDC | Potential National Drug Code field |
| CIP.xlsx | Sheet1 | Description | str | Megestrol Acetate OS 40mg/mL, 240 | 0 | 10 | UNKNOWN | UNKNOWN |
| CIP.xlsx | Sheet1 | Comments | str | 36K wk of 08/17 | 0 | 10 | UNKNOWN | UNKNOWN |
| CIP.xlsx | Sheet1 | Customer ETA | str | wk 8/17 | 0 | 6 | UNKNOWN | Potential customer/account field |

## MOQ.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOQ.xlsx | Sheet1 | HANA Material | int64 | 3011903 | 0 | 4 | Material Number | Potential material identifier or description |
| MOQ.xlsx | Sheet1 | NDC code | int64 | 64380020101 | 0 | 4 | NDC | Potential National Drug Code field |
| MOQ.xlsx | Sheet1 | Material Description | str | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | 0 | 4 | UNKNOWN | Potential material identifier or description |
| MOQ.xlsx | Sheet1 | MOQ  | int64 | 24 | 0 | 3 | UNKNOWN | UNKNOWN |

## Open_Order_Summary.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Open_Order_Summary.xlsx | Sheet1 | Create Date | str | 7/24/26 | 0 | 3 | UNKNOWN | Potential date field |
| Open_Order_Summary.xlsx | Sheet1 | PH_ORD_DATE | str | 7/24/26 | 0 | 4 | UNKNOWN | Potential date field |
| Open_Order_Summary.xlsx | Sheet1 | Current Date | str | 7/30/26 | 0 | 1 | UNKNOWN | Potential date field |
| Open_Order_Summary.xlsx | Sheet1 | No of days | int64 | 6 | 0 | 3 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | Aging | str | >4 days | 0 | 3 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | PH_PKT_CTRL_NBR | int64 | 8061682605 | 0 | 5 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | Uniq ID | int64 | 1100005792 | 0 | 5 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | SO# | int64 | 3612002867 | 0 | 5 | Sales Order | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | PO# | str | C7188832NLC | 0 | 5 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | Pickticket Status | str | In Picking | 0 | 3 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | SKU | str | 64380-201-01 | 0 | 3 | SKU | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | IM_SKU_DESC | str | Amlo/Hctz/Valsar Tab 10/25/320 Mg 30 | 0 | 3 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | SPI/CR | str | CR | 0 | 2 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | x | str | 64380-201-01Cardinal | 0 | 6 | Lookup | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | PH_SOLDTO_NAME | str | CAH GLOBAL CONTRACTING COMPANY LTD | 0 | 4 | Customer | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | Customer Group | str | Cardinal | 0 | 4 | UNKNOWN | Potential customer/account field |
| Open_Order_Summary.xlsx | Sheet1 | Street Address | str | 5995 COMMERCE CENTER DRIVE | 0 | 4 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | City | str | GROVEPORT | 0 | 4 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | PH_SHIPTO_STATE | str | OH | 0 | 2 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 |  Total  | int64 | 624 | 0 | 5 | UNKNOWN | UNKNOWN |
| Open_Order_Summary.xlsx | Sheet1 | UPS | str | BRB | 0 | 1 | UNKNOWN | UNKNOWN |

## raw_OB.xlsx

### UOB

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw_OB.xlsx | UOB | Sales Order No. | int64 | 3612003019 | 0 | 5 | Sales Order | UNKNOWN |
| raw_OB.xlsx | UOB | Item No. | int64 | 30 | 0 | 5 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Matl.Code | int64 | 3011973 | 0 | 2 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | NDC Code | int64 | 64380018701 | 0 | 2 | NDC | Potential National Drug Code field |
| raw_OB.xlsx | UOB | Material Description | str | ZAFIRLUKAST TABS 10MG 60 | 0 | 2 | UNKNOWN | Potential material identifier or description |
| raw_OB.xlsx | UOB | Total Stock In-hand | int64 | 19512 | 0 | 2 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | PackSize(MOQ) | int64 | 24 | 0 | 1 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Sales Order Qty | int64 | 24 | 0 | 3 | Sales Order | Potential quantity field |
| raw_OB.xlsx | UOB | Sales Qty MTD | int64 | 168 | 0 | 2 | UNKNOWN | Potential quantity field |
| raw_OB.xlsx | UOB | Forecast Qty | int64 | 122 | 0 | 2 | UNKNOWN | Potential quantity field |
| raw_OB.xlsx | UOB | Sold-to party | int64 | 9700378 | 0 | 1 | Sold-to Party | Potential customer/account field |
| raw_OB.xlsx | UOB | Sold-to party Name | str | KROGER | 0 | 1 | Customer | Potential customer/account field |
| raw_OB.xlsx | UOB | S.O. Type | str | ZTRU | 0 | 1 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Unit Price | float64 | 8.19 | 0 | 2 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Sales Value (FC) | float64 | 196.56 | 0 | 4 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | WAC/BG price in EDI | float64 | 8.19 | 0 | 2 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | PO number | int64 | 21918 | 0 | 5 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | PO date | datetime64[us] | 2026-07-30 00:00:00 | 0 | 1 | UNKNOWN | Potential date field |
| raw_OB.xlsx | UOB | Ship-to party | int64 | 9800166 | 0 | 3 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Ship-to party Name | str | KROGER_BLUFFTON | 0 | 3 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Street | str | 1111 SOUTH ADAMS STREET | 0 | 3 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | City | str | BLUFFTON | 0 | 3 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Region | str | Indiana | 0 | 3 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Postal Code | int64 | 46714 | 0 | 3 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Country | str | US | 0 | 1 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Reas. Rej. | str | Y6 | 0 | 1 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Reason for Rejection | str | ZUS Y6 Block | 0 | 1 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Material Blk | str | X | 0 | 1 | UNKNOWN | Potential material identifier or description |
| raw_OB.xlsx | UOB | Floor limit Blk | float64 |  | 8 | 0 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Multiple of MOQ Blk | float64 |  | 8 | 0 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | Expected Price Blk | float64 |  | 8 | 0 | UNKNOWN | UNKNOWN |
| raw_OB.xlsx | UOB | DEA Number (Customer Master) | str | PP0220828 | 0 | 3 | UNKNOWN | Potential customer/account field |
| raw_OB.xlsx | UOB | Req. Delivery Date | datetime64[us] | 2026-08-06 00:00:00 | 0 | 1 | UNKNOWN | Potential date field |
| raw_OB.xlsx | UOB | SOM Indc. | float64 |  | 8 | 0 | UNKNOWN | Potential National Drug Code field |

## Strend.xlsx

### Sheet1

| Workbook | Worksheet | Exact Column Name | Detected Data Type | Sample Value | Null Count | Unique Count | Potential Join Key | Potential Business Meaning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Strend.xlsx | Sheet1 | NDC Code | int64 | 64380020101 | 0 | 4 | NDC | Potential National Drug Code field |
| Strend.xlsx | Sheet1 | Material Description | str | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | 0 | 4 | UNKNOWN | Potential material identifier or description |
| Strend.xlsx | Sheet1 | Product | str | AVH | 0 | 4 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 | Count | int64 | 30 | 0 | 2 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 | SPI/CR | str | CR | 0 | 2 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 | Sold-to party Name | str | CENCORA GLOBAL PROCUREMENT | 0 | 53 | Customer | Potential customer/account field |
| Strend.xlsx | Sheet1 | Cust Group | str | WBAD | 0 | 23 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Cont ID  | str | ABCS0614 | 0 | 23 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 | x | str | 64380020101CENCORA GLOBAL PROCUREMENT | 0 | 101 | Lookup | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jul-22  | str |  -    | 45 | 5 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Aug-22  | str |  336  | 45 | 6 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Sep-22  | str |  1,056  | 45 | 7 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Oct-22  | str |  696  | 45 | 7 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Nov-22  | str |  360  | 45 | 12 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Dec-22  | str |  864  | 45 | 11 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jan-23  | str |  1,104  | 45 | 13 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Feb-23  | str |  1,152  | 45 | 14 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Mar-23  | str |  1,200  | 45 | 14 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Apr-23  | str |  1,200  | 45 | 15 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  May-23  | str |  1,440  | 45 | 17 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  June-23  | str |  1,488  | 45 | 19 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jul-23  | str |  1,032  | 45 | 17 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Aug-23  | str |  1,344  | 45 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Sept-23  | str |  1,440  | 45 | 18 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Oct-23  | str |  1,368  | 45 | 17 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Nov-23  | str |  1,512  | 45 | 17 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Dec-23  | str |  1,200  | 45 | 19 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jan-24  | str |  1,560  | 45 | 11 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Feb-24  | str |  1,368  | 45 | 18 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Mar-24  | str |  1,776  | 45 | 19 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Apr-24  | str |  1,848  | 45 | 14 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  May-24  | str |  2,064  | 44 | 18 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  June-24  | str |  1,152  | 39 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  July-24  | str |  1,488  | 36 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Aug-24  | str |  2,160  | 35 | 15 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Sept-24  | str |  1,680  | 35 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Oct-24  | str |  1,896  | 34 | 17 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Nov-24  | str |  1,632  | 33 | 15 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Dec 2024  | str |  2,928  | 33 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jan-25  | str |  1,464  | 33 | 14 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Feb-25  | str |  2,472  | 32 | 15 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Mar-25  | str |  1,344  | 32 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Apr-25  | str |  -    | 31 | 18 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  May 25  | str |  1,920  | 31 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  June-25  | str |  2,520  | 30 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  July-25  | str |  1,032  | 26 | 18 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Aug-25  | str |  48  | 25 | 14 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Sept-25  | str |  -    | 20 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Oct-25  | str |  -    | 18 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Nov-25  | str |  576  | 16 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Dec-25  | str |  120  | 15 | 22 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jan-26  | str |  120  | 14 | 18 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Feb-26  | str |  504  | 12 | 21 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Mar-26  | str |  240  | 9 | 22 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Apr-26  | str |  240  | 6 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  May-26  | str |  48  | 6 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  June-26  | str |  168  | 4 | 22 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Jul-26  | str |  144  | 0 | 16 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Open Order 7-29-2026  | str |  96  | 0 | 6 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Released Order 7-29-2026  | str |  -    | 0 | 3 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Pending invoice-SAP 7-29-2026  | str |  72  | 0 | 6 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  July -26  | str |  312  | 0 | 20 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  July'26- Forecast  | str |  250  | 3 | 50 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  Avg Jan'26 to June'26  | str |  220  | 1 | 41 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  %  | str | 65% | 0 | 23 | UNKNOWN | UNKNOWN |
| Strend.xlsx | Sheet1 |  MTD-Target  | str |  220  | 1 | 41 | UNKNOWN | UNKNOWN |
