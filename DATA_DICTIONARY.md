# DATA_DICTIONARY

Source scan of Excel workbooks under `D:\Jayanth`.


## 07-30_inv.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 07-30_inv.xlsx | Sheet1 | NDC | Integer | 64380016101 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | SKU | Text | 64380-161-01 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Description | Text | Valganciclovir Tablets 450mg 60ct | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Lot | Text | 7262830A | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Expiration Date | Integer | 46507 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Hold Codes | Text | SD,HD | Yes |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Product Status | Text |  | Yes |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Actual Quantity | Integer | 24 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Allocated Quantity | Boolean | 0 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | Inventory | Integer | 24 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | On Hand Damaged | Boolean | 0 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | On Hand Hold | Integer | 24 | No |  | NDC; SKU |
| 07-30_inv.xlsx | Sheet1 | On Hand Misc | Boolean | 0 | No |  | NDC; SKU |

## Awards.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Awards.xlsx | Sheet1 | Lookup | Text | 64380072701CAH GLOBAL CONTRACTING COMPANY LTD | No |  | Lookup; NDC |
| Awards.xlsx | Sheet1 | NDC | Integer | 64380072701 | No |  | Lookup; NDC |
| Awards.xlsx | Sheet1 | Product | Text | Gaba Tabs | No |  | Lookup; NDC |
| Awards.xlsx | Sheet1 | Description | Text | Gabapentin Tablets 600Mg 100Ct | No |  | Lookup; NDC |
| Awards.xlsx | Sheet1 | Customer | Text | Cardinal Health | No |  | Lookup; NDC |
| Awards.xlsx | Sheet1 | Award Type | Text | Backup | Yes |  | Lookup; NDC |
| Awards.xlsx | Sheet1 | Sold to party | Text | CAH GLOBAL CONTRACTING COMPANY LTD | No |  | Lookup; NDC |

## Buying_groups.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Buying_groups.xlsx | Sheet1 | Customer | Text | American Health Packaging | No |  | Customer |
| Buying_groups.xlsx | Sheet1 | Customer buying group | Text | AHP | No |  | Customer |

## CIP.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CIP.xlsx | Sheet1 | NDC | Integer | 64380016001 | No |  | NDC |
| CIP.xlsx | Sheet1 | Description | Text | Megestrol Acetate OS 40mg/mL, 240 | No |  | NDC |
| CIP.xlsx | Sheet1 | Comments | Text | 36K wk of 08/17 | No |  | NDC |
| CIP.xlsx | Sheet1 | Customer ETA | Text | wk 8/17 | No |  | NDC |

## Headers.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Headers.xlsx | Sheet1 | Sales Order No. | Text | Summary | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Item No. | Text | Sold-to party Name | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Lookup | Text | Lookup | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Matl._x000d_
Code | Text | NDC Code | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | NDC Code | Text | Max of UPS Inventory | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Material Description | Text | Sum of Sales Order Qty | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Total Stock _x000d_
In-hand | Text | Max of Sales Qty MTD | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | UPS Inventory | Text | Max of Forecast Qty | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Pack Size (MOQ) | Text | John | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Sales Order Qty | Text | Apr | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Sales Qty MTD | Text | May | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Forecast Qty | Text | Jun | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Sold-to party | Text | Avg | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Sold-to party Name | Text | Buying Group | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Action | Text | Award Type | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | S.O. Type | Text | SC Comments | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 |  Unit Price  | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 |  Sales Value (FC)  | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | WAC/BG price in EDI | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | PO Number | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | PO Date | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Ship-to party | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Ship-to party Name | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Street | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | City | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Region | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Postal Code | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Country | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Reas. Rej. | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Reason for Rejection | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Material Blk | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Floor limit Blk | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Multiple of MOQ Blk | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Expected Price Blk | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | DEA Number (Customer Master) | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | Req. Delivery Date | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |
| Headers.xlsx | Sheet1 | SOM Indc. | Text |  | Yes |  | Sales Order No.; Item No.; Matl.Code; NDC Code |

## Mat_Desc,_MOQ_,_Material_#.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mat_Desc,_MOQ_,_Material_#.xlsx | Sheet1 | HANA Material | Integer | 3011903 | No |  | NDC code; HANA Material |
| Mat_Desc,_MOQ_,_Material_#.xlsx | Sheet1 | NDC code | Integer | 64380020101 | No |  | NDC code; HANA Material |
| Mat_Desc,_MOQ_,_Material_#.xlsx | Sheet1 | Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | NDC code; HANA Material |
| Mat_Desc,_MOQ_,_Material_#.xlsx | Sheet1 | MOQ  | Integer | 24 | No |  | NDC code; HANA Material |

## obook.xlsx

### Mat Desc, MOQ , Material #

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | Mat Desc, MOQ , Material # | HANA Material | Integer | 3011903 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Mat Desc, MOQ , Material # | NDC code | Integer | 64380020101 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Mat Desc, MOQ , Material # | Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Mat Desc, MOQ , Material # | MOQ  | Integer | 24 | No |  | Sales Order No.; Item No. |
### 07-30 inv

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | 07-30 inv | NDC | Integer | 64380016101 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | SKU | Text | 64380-161-01 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Description | Text | Valganciclovir Tablets 450mg 60ct | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Lot | Text | 7262830A | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Expiration Date | Integer | 46507 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Hold Codes | Text | SD,HD | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Product Status | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Actual Quantity | Integer | 24 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Allocated Quantity | Boolean | 0 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | Inventory | Integer | 24 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | On Hand Damaged | Boolean | 0 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | On Hand Hold | Integer | 24 | No |  | Sales Order No.; Item No. |
| obook.xlsx | 07-30 inv | On Hand Misc | Boolean | 0 | No |  | Sales Order No.; Item No. |
### CIP

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | CIP | NDC | Integer | 64380016001 | No |  | Sales Order No.; Item No. |
| obook.xlsx | CIP | Description | Text | Megestrol Acetate OS 40mg/mL, 240 | No |  | Sales Order No.; Item No. |
| obook.xlsx | CIP | Comments | Text | 36K wk of 08/17 | No |  | Sales Order No.; Item No. |
| obook.xlsx | CIP | Customer ETA | Text | wk 8/17 | No |  | Sales Order No.; Item No. |
### Strend

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | Strend | NDC Code | Integer | 64380020101 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Product | Text | AVH | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Count | Integer | 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | SPI/CR | Text | CR | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Sold-to party Name | Text | CENCORA GLOBAL PROCUREMENT | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Cust Group | Text | WBAD | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Cont ID | Text | ABCS0614 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | x | Text | 64380020101CENCORA GLOBAL PROCUREMENT | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jul-22 | Integer | 0.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Aug-22 | Integer | 336.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Sep-22 | Integer | 1056.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Oct-22 | Integer | 696.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Nov-22 | Integer | 360.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Dec-22 | Integer | 864.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jan-23 | Integer | 1104.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Feb-23 | Integer | 1152.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Mar-23 | Integer | 1200.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Apr-23 | Integer | 1200.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | May-23 | Integer | 1440.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | June-23 | Integer | 1488.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jul-23 | Integer | 1032.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Aug-23 | Integer | 1344.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Sept-23 | Integer | 1440.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Oct-23 | Integer | 1368.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Nov-23 | Integer | 1512.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Dec-23 | Integer | 1200.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jan-24 | Integer | 1560.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Feb-24 | Integer | 1368.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Mar-24 | Integer | 1776.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Apr-24 | Integer | 1848.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | May-24 | Integer | 2064.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | June-24 | Integer | 1152.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | July-24 | Integer | 1488.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Aug-24 | Integer | 2160.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Sept-24 | Integer | 1680.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Oct-24 | Integer | 1896.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Nov-24 | Integer | 1632.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Dec 2024 | Integer | 2928.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jan-25 | Integer | 1464.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Feb-25 | Integer | 2472.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Mar-25 | Integer | 1344.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Apr-25 | Integer | 0.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | May 25 | Integer | 1920.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | June-25 | Integer | 2520.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | July-25 | Integer | 1032.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Aug-25 | Integer | 48.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Sept-25 | Integer | 0.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Oct-25 | Integer | 0.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Nov-25 | Integer | 576.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Dec-25 | Integer | 120.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jan-26 | Integer | 120.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Feb-26 | Integer | 504.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Mar-26 | Integer | 240.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Apr-26 | Integer | 240.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | May-26 | Integer | 48.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | June-26 | Integer | 168.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Jul-26 | Integer | 144 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Open Order 7-29-2026 | Integer | 96 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Released Order 7-29-2026 | Integer | 0 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Pending invoice-SAP 7-29-2026 | Integer | 72 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | July -26 | Integer | 312 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | July'26- Forecast | Decimal | 250.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | Avg Jan'26 to June'26 | Decimal | 220.0 | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | % | Decimal | 0.6545454545454545 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Strend | MTD-Target | Decimal | 220.0 | Yes |  | Sales Order No.; Item No. |
### Open Order Summary

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | Open Order Summary | Create Date | Date | 2026-07-24 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | PH_ORD_DATE | Date | 2026-07-24 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Current Date | Date | 2026-07-30 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | No of days | Integer | 6 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Aging | Text | >4 days | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | PH_PKT_CTRL_NBR | Integer | 8061682605 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Uniq ID | Integer | 1100005792 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | SO# | Integer | 3612002867 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | PO# | Text | C7188832NLC | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Pickticket Status | Text | In Picking | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | SKU | Text | 64380-201-01 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | IM_SKU_DESC | Text | Amlo/Hctz/Valsar Tab 10/25/320 Mg 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | SPI/CR | Text | CR | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | x | Text | 64380-201-01Cardinal | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | PH_SOLDTO_NAME | Text | CAH GLOBAL CONTRACTING COMPANY LTD | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Customer Group | Text | Cardinal | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Street Address | Text | 5995 COMMERCE CENTER DRIVE | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | City | Text | GROVEPORT | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | PH_SHIPTO_STATE | Text | OH | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | Total | Integer | 624 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Open Order Summary | UPS | Text | BRB | No |  | Sales Order No.; Item No. |
### Buying groups

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | Buying groups | Customer | Text | American Health Packaging | No |  | Sales Order No.; Item No. |
| obook.xlsx | Buying groups | Customer buying group | Text | AHP | No |  | Sales Order No.; Item No. |
### Awards

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | Awards | Lookup | Text | 64380072701CAH GLOBAL CONTRACTING COMPANY LTD | No |  | Sales Order No.; Item No. |
| obook.xlsx | Awards | NDC | Integer | 64380072701 | No |  | Sales Order No.; Item No. |
| obook.xlsx | Awards | Product | Text | Gaba Tabs | No |  | Sales Order No.; Item No. |
| obook.xlsx | Awards | Description | Text | Gabapentin Tablets 600Mg 100Ct | No |  | Sales Order No.; Item No. |
| obook.xlsx | Awards | Customer | Text | Cardinal Health | No |  | Sales Order No.; Item No. |
| obook.xlsx | Awards | Award Type | Text | Backup | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Awards | Sold to party | Text | CAH GLOBAL CONTRACTING COMPANY LTD | No |  | Sales Order No.; Item No. |
### Headers

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | Headers | Sales Order No. | Text | Summary | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Item No. | Text | Sold-to party Name | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Lookup | Text | Lookup | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Matl.
Code | Text | NDC Code | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | NDC Code | Text | Max of UPS Inventory | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Material Description | Text | Sum of Sales Order Qty | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Total Stock 
In-hand | Text | Max of Sales Qty MTD | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | UPS Inventory | Text | Max of Forecast Qty | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Pack Size (MOQ) | Text | John | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Sales Order Qty | Text | Apr | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Sales Qty MTD | Text | May | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Forecast Qty | Text | Jun | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Sold-to party | Text | Avg | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Sold-to party Name | Text | Buying Group | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Action | Text | Award Type | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | S.O. Type | Text | SC Comments | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Unit Price | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Sales Value (FC) | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | WAC/BG price in EDI | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | PO Number | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | PO Date | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Ship-to party | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Ship-to party Name | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Street | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | City | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Region | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Postal Code | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Country | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Reas. Rej. | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Reason for Rejection | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Material Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Floor limit Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Multiple of MOQ Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Expected Price Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | DEA Number (Customer Master) | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | Req. Delivery Date | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | Headers | SOM Indc. | Text |  | Yes |  | Sales Order No.; Item No. |
### POB

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | POB |  Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Sold-to party Name | Text | EXPRESS SCRIPTS | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Lookup | Text | 64380020101EXPRESS SCRIPTS | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | NDC Code | Integer | 64380020101 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Max of UPS Inventory | Integer | 21696 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Sum of Sales Order Qty | Integer | 72 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Max of Sales Qty MTD | Integer | 432 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Max of Forecast Qty | Integer | 366 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Comments | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Apr | Integer | 504 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | May | Integer | 360 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Jun | Integer | 288 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Avg | Integer | 384 | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Buying Group | Text | Econdisc | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | Award Type | Text | Primary | No |  | Sales Order No.; Item No. |
| obook.xlsx | POB | SC Comments | Text |  | Yes |  | Sales Order No.; Item No. |
### sales summ

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | sales summ | Sales Order No. | Integer | 3612002936 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Item No. | Integer | 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Lookup | Text | 64380020101EXPRESS SCRIPTS | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Matl.
Code | Integer | 3011903 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | NDC Code | Integer | 64380020101 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Total Stock 
In-hand | Integer | 23061 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | UPS Inventory | Integer | 21696 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Pack Size (MOQ) | Integer | 24 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Sales Order Qty | Integer | 72 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Sales Qty MTD | Integer | 432 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Forecast Qty | Integer | 366 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Sold-to party | Integer | 9700306 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Sold-to party Name | Text | EXPRESS SCRIPTS | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Action | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | S.O. Type | Text | ZTRU | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Unit Price | Decimal | 160.06 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Sales Value (FC) | Decimal | 11524.32 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | WAC/BG price in EDI | Decimal | 160.06 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | PO Number | Text | 1036729-2331 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | PO Date | Date | 2026-07-28 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Ship-to party | Integer | 9800112 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Ship-to party Name | Text | EXPRESS SCRIPTS_BURLINGTON | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Street | Text | 2040 ROUTE 130 NORTH | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | City | Text | BURLINGTON | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Region | Text | New Jersey | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Postal Code | Integer | 8016 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Country | Text | US | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Reas. Rej. | Text | Y6 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Reason for Rejection | Text | ZUS Y6 Block | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Material Blk | Text | X | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Floor limit Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Multiple of MOQ Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Expected Price Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | DEA Number (Customer Master) | Text | FE4492738 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | Req. Delivery Date | Date | 2026-07-28 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | sales summ | SOM Indc. | Text |  | Yes |  | Sales Order No.; Item No. |
### raw OB

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| obook.xlsx | raw OB | Sales Order Qty | Integer | 24 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Sales Qty MTD | Integer | 168 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Forecast Qty | Integer | 122 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Sold-to party | Integer | 9700378 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Sold-to party Name | Text | KROGER | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | S.O. Type | Text | ZTRU | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Unit Price | Decimal | 8.19 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Sales Value (FC) | Decimal | 196.56 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | WAC/BG price in EDI | Decimal | 8.19 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | PO number | Integer | 21918 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | PO date | Date | 2026-07-30 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Ship-to party | Integer | 9800166 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Ship-to party Name | Text | KROGER_BLUFFTON | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Street | Text | 1111 SOUTH ADAMS STREET | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | City | Text | BLUFFTON | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Region | Text | Indiana | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Postal Code | Integer | 46714 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Country | Text | US | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Reas. Rej. | Text | Y6 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Reason for Rejection | Text | ZUS Y6 Block | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Material Blk | Text | X | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Floor limit Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Multiple of MOQ Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Expected Price Blk | Text |  | Yes |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | DEA Number (Customer Master) | Text | PP0220828 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | Req. Delivery Date | Date | 2026-08-06 00:00:00 | No |  | Sales Order No.; Item No. |
| obook.xlsx | raw OB | SOM Indc. | Text |  | Yes |  | Sales Order No.; Item No. |

## Open_Order_Summary.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Open_Order_Summary.xlsx | Sheet1 | Create Date | Date | 7/24/26 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | PH_ORD_DATE | Date | 7/24/26 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | Current Date | Date | 7/30/26 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | No of days | Integer | 6 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | Aging | Text | >4 days | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | PH_PKT_CTRL_NBR | Integer | 8061682605 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | Uniq ID | Integer | 1100005792 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | SO# | Integer | 3612002867 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | PO# | Text | C7188832NLC | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | Pickticket Status | Text | In Picking | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | SKU | Text | 64380-201-01 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | IM_SKU_DESC | Text | Amlo/Hctz/Valsar Tab 10/25/320 Mg 30 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | SPI/CR | Text | CR | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | x | Text | 64380-201-01Cardinal | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | PH_SOLDTO_NAME | Text | CAH GLOBAL CONTRACTING COMPANY LTD | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | Customer Group | Text | Cardinal | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | Street Address | Text | 5995 COMMERCE CENTER DRIVE | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | City | Text | GROVEPORT | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | PH_SHIPTO_STATE | Text | OH | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 |  Total  | Integer | 624 | No |  | SO#; SKU; PH_SOLDTO_NAME |
| Open_Order_Summary.xlsx | Sheet1 | UPS | Text | BRB | No |  | SO#; SKU; PH_SOLDTO_NAME |

## POB.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| POB.xlsx | Sheet1 |  Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 | Sold-to party Name | Text | EXPRESS SCRIPTS | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 | Lookup | Text | 64380020101EXPRESS SCRIPTS | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 | NDC Code | Integer | 64380020101 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Max of UPS Inventory  | Integer | 21696 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Sum of Sales Order Qty  | Integer | 72 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Max of Sales Qty MTD  | Integer | 432 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Max of Forecast Qty  | Integer | 366 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Comments  | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Apr  | Integer | 504 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  May  | Integer | 360 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Jun  | Integer | 288 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 |  Avg  | Integer | 384 | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 | Buying Group | Text | Econdisc | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 | Award Type | Text | Primary | No |  | Lookup; NDC Code; Sold-to party Name |
| POB.xlsx | Sheet1 | SC Comments | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |

## raw_OB.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| raw_OB.xlsx | Sheet1 | Sales Order Qty | Integer | 24.0 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Sales Qty MTD | Integer | 168.0 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Forecast Qty | Integer | 122.0 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Sold-to party | Integer | 9700378 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Sold-to party Name | Text | KROGER | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | S.O. Type | Text | ZTRU | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Unit Price | Decimal | 8.19 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Sales Value (FC) | Decimal | 196.56 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | WAC/BG price in EDI | Decimal | 8.19 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | PO number | Integer | 21918 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | PO date | Date | 7/30/26 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Ship-to party | Integer | 9800166 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Ship-to party Name | Text | KROGER_BLUFFTON | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Street | Text | 1111 SOUTH ADAMS STREET | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | City | Text | BLUFFTON | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Region | Text | Indiana | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Postal Code | Integer | 46714 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Country | Text | US | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Reas. Rej. | Text | Y6 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Reason for Rejection | Text | ZUS Y6 Block | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Material Blk | Text | X | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Floor limit Blk | Text |  | Yes |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Multiple of MOQ Blk | Text |  | Yes |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Expected Price Blk | Text |  | Yes |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | DEA Number (Customer Master) | Text | PP0220828 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | Req. Delivery Date | Date | 8/6/26 | No |  | Sales Order Qty; Sold-to party; Ship-to party |
| raw_OB.xlsx | Sheet1 | SOM Indc. | Text |  | Yes |  | Sales Order Qty; Sold-to party; Ship-to party |

## sales_summ.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sales_summ.xlsx | Sheet1 | Sales Order No. | Integer | 3612002936 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Item No. | Integer | 30 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Lookup | Text | 64380020101EXPRESS SCRIPTS | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Matl._x000d_
Code | Integer | 3011903 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | NDC Code | Integer | 64380020101 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Total Stock _x000d_
In-hand | Integer | 23,061 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | UPS Inventory | Integer | 21,696 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Pack Size (MOQ) | Integer | 24 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Sales Order Qty | Integer | 72 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Sales Qty MTD | Integer | 432 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Forecast Qty | Integer | 366 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Sold-to party | Integer | 9700306 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Sold-to party Name | Text | EXPRESS SCRIPTS | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Action | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | S.O. Type | Text | ZTRU | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 |  Unit Price  | Decimal | 160.06 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 |  Sales Value (FC)  | Decimal | 11,524.32 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | WAC/BG price in EDI | Decimal | 160.06 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | PO Number | Text | 1036729-2331 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | PO Date | Date | 7/28/26 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Ship-to party | Integer | 9800112 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Ship-to party Name | Text | EXPRESS SCRIPTS_BURLINGTON | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Street | Text | 2040 ROUTE 130 NORTH | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | City | Text | BURLINGTON | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Region | Text | New Jersey | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Postal Code | Integer | 8016 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Country | Text | US | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Reas. Rej. | Text | Y6 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Reason for Rejection | Text | ZUS Y6 Block | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Material Blk | Text | X | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Floor limit Blk | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Multiple of MOQ Blk | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Expected Price Blk | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | DEA Number (Customer Master) | Text | FE4492738 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | Req. Delivery Date | Date | 7/28/26 | No |  | Lookup; NDC Code; Sold-to party Name |
| sales_summ.xlsx | Sheet1 | SOM Indc. | Text |  | Yes |  | Lookup; NDC Code; Sold-to party Name |

## Strend.xlsx

### Sheet1

| Workbook Name | Worksheet Name | Exact Column Name | Data Type (inferred) | Sample Value | Nullable | Duplicate Column Names | Recommended Join Key(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Strend.xlsx | Sheet1 | NDC Code | Integer | 64380020101 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | Material Description | Text | AMLO/HCTZ/VALSAR TAB 10/25/320 MG 30 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | Product | Text | AVH | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | Count | Integer | 30 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | SPI/CR | Text | CR | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | Sold-to party Name | Text | CENCORA GLOBAL PROCUREMENT | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | Cust Group | Text | WBAD | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Cont ID  | Text | ABCS0614 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 | x | Text | 64380020101CENCORA GLOBAL PROCUREMENT | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jul-22  | Text | - | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Aug-22  | Text | 336 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Sep-22  | Text | 1,056 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Oct-22  | Text | 696 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Nov-22  | Text | 360 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Dec-22  | Text | 864 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jan-23  | Text | 1,104 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Feb-23  | Text | 1,152 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Mar-23  | Text | 1,200 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Apr-23  | Text | 1,200 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  May-23  | Text | 1,440 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  June-23  | Text | 1,488 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jul-23  | Text | 1,032 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Aug-23  | Text | 1,344 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Sept-23  | Text | 1,440 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Oct-23  | Text | 1,368 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Nov-23  | Text | 1,512 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Dec-23  | Text | 1,200 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jan-24  | Text | 1,560 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Feb-24  | Text | 1,368 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Mar-24  | Text | 1,776 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Apr-24  | Text | 1,848 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  May-24  | Text | 2,064 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  June-24  | Text | 1,152 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  July-24  | Text | 1,488 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Aug-24  | Text | 2,160 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Sept-24  | Text | 1,680 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Oct-24  | Text | 1,896 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Nov-24  | Text | 1,632 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Dec 2024  | Text | 2,928 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jan-25  | Text | 1,464 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Feb-25  | Text | 2,472 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Mar-25  | Text | 1,344 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Apr-25  | Text | - | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  May 25  | Text | 1,920 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  June-25  | Text | 2,520 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  July-25  | Text | 1,032 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Aug-25  | Text | 48 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Sept-25  | Text | - | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Oct-25  | Text | - | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Nov-25  | Text | 576 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Dec-25  | Text | 120 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jan-26  | Text | 120 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Feb-26  | Text | 504 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Mar-26  | Text | 240 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Apr-26  | Text | 240 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  May-26  | Text | 48 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  June-26  | Text | 168 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Jul-26  | Text | 144 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Open Order 7-29-2026  | Text | 96 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Released Order 7-29-2026  | Text | - | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Pending invoice-SAP 7-29-2026  | Text | 72 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  July -26  | Text | 312 | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  July'26- Forecast  | Text | 250 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  Avg Jan'26 to June'26  | Text | 220 | Yes |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  %  | Text | 65% | No |  | NDC Code; Sold-to party Name |
| Strend.xlsx | Sheet1 |  MTD-Target  | Text | 220 | Yes |  | NDC Code; Sold-to party Name |
