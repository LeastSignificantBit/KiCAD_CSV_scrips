# KiCAD_CSV_scrips
These are two slightly modified scripts used to export and import BOM for easy external editing.

The idea is to help out when using KiCost by using an external spreadsheet program to fill in all those manf# fields.

Usually this can be a tedious process, editing them one by one, but with these scripts you have the alternative to work with the field in a spreadsheet.

The bom_.py script was modified to be used together with kicost (it uses the manf# field) and I added sorting for a more intuitive experience.
The csv2sch.py scipt I only modified to not put "~" instead of empty field values. 

## Usage
1. Create a scematic and save it.
2. Add the bom_.py script to the BOM export scripts.
3. Modify the "Command line" expression to end like: [..] bom_csv_w_manf.py" "%I" "%O.csv"
   This is done so that the exported file gets the csv file ending.
4. Click "Generate" and check that the export is successful.
5. Close the scematic in order not to do any changes while you are editing it externaly.
5. Open the exported csv in your favourite Spreadsheet editor and edit the fields to your liking.
6. Save the csv, making sure it is still tab separated.
7. Import the changes using csv2sch.py e.g.:
csv2sch.py editedspreadsheet.csv *.sch
8. Open the modified schematic in KiCAd again
9. Done

## Credit
I shamelessly stole both these scripts from either the Kicad source tree and a post on kicad.info
The only thing I did was collect them, test and changed some small bits in order for them to work in a way I like.
