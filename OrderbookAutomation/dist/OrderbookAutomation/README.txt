========================================================================
 Orderbook Automation - Business User Guide
========================================================================

WHAT THIS TOOL DOES
--------------------
This application reads the daily Excel workbooks you provide, validates
and profiles them, builds the Business Master Dataset, and produces the
final Sales Summary and POB (Purchase Order Book) reports.

FOLDER STRUCTURE
-----------------
OrderbookAutomation\
  OrderbookAutomation.exe   <- Double-click this to run the tool
  input\                    <- Place your daily Excel workbooks here
  output\                   <- Generated reports appear here
  logs\                     <- Technical log files (for support use)
  docs\                     <- Auto-generated data dictionary/analysis docs
  README.txt                <- This file

HOW TO RUN
-----------
1. Copy your daily Excel files into the "input" folder.
   - File names do NOT need to match any fixed pattern (e.g. you can use
     dated names like "raw_OB_2026-08-14.xlsx"). The tool automatically
     identifies each file by its column headers/worksheet contents.
   - Column order within a file does not matter; columns are matched by
     name, not position.
2. Double-click "OrderbookAutomation.exe".
3. A console window will open and show progress messages.
4. When it finishes, you will see:

     Orderbook processing completed successfully.
     Output folder:
     <path>\output

5. Open the "output" folder to find:
   - POB.xlsx              (final Purchase Order Book)
   - Sales_Summary.xlsx    (final Sales Summary report)
   - Business_Master_Data.xlsx
   - Derived_Data.xlsx
   - Workbook_Profile.xlsx

IF SOMETHING GOES WRONG
-------------------------
- The console window will print a short, clear error message.
- Full technical details are always written to the "logs" folder
  (phase1.log). Please send this log file to support if you need help.
- Your original input files in the "input" folder are never modified.

NOTES
------
- You can run the tool as many times as you like; each run overwrites
  the files in the "output" folder with fresh results.
- The "input" folder is never written to by the application.
- This package can be copied to any folder or machine; no installation
  or Python setup is required.

========================================================================
