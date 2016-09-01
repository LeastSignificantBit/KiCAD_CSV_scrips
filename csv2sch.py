#! /usr/bin/env python2
#-*- coding: utf8 -*-

"""Read a .tsv and import it into multiple kicad sheets."""

"""
Stolen from https://gist.github.com/Caerbannog/540376e8583d8f73addf
refered to in the thread: https://forum.kicad.info/t/towards-better-bom-management/1979/8  by the user caer

Scenario:
- Export the BOM from EEschema as .csv
- Edit it in a spreadsheet program (Excel, Calc) or as text. You can add columns (Manufacturer, Voltage specs, ...)
- Save it back as .tsv/.csv (tab separated values, this is the easiest export of spreadsheet programs)
- Run ./tsv2sch.py exported_file.tsv kicad_sheet1.sch kicad_sheet2.sch to import the changes back into KiCad.

Faster way to update all your project sheets: ./tsv2sch.py exported_file.tsv project/*.sch
You can customize some of the script (columns to ignore for instance).
"""
import sys, shutil
import csv, re

# CSV columns that will be ignored.
IGNORED_COLUMNS = [ "sheetName", 'Reference', "Designator", "Quantity", ""]
# KiCad components that will be ignored.
IGNORED_VALUES = [ "NC", "do-not-populate" ]

# Fields that have no name in the SCH (implicit in KiCad).
FIXED_FIELD_NAMES = ['Reference', 'Value', 'Footprint', 'Datasheet']

def update_components(content, components, new_fields, untracked_fields):
    new_sch = ""
    lines = iter(content.splitlines())
    current_comp = None
    untracked_references = set()
    components_keys = set(components.keys()) # Save the keys before we start removing from the dict.
    
    for line in lines:
        if not line.startswith("F "):
            # If there are remaining fields, append them to finish the current field list.
            if current_comp is not None:
                for field_name in current_comp: # These are new fields
                    field_value = current_comp[field_name]
                    new_fields.add(field_name)
                    current_field_num += 1
                    new_sch += 'F %d "%s" H %s %s %s  0001 C CNN "%s"\n' % (current_field_num, field_value, posx, posy, 60, field_name) # Reuse previous position
                current_comp = None
            new_sch += line + "\n"
        else:
            # This is a component field.
            field_num, field_value, hori, posx, posy, size, flags, line_end, field_name = re.match(r'F (\d+) "(.*)" (H|V) (\d+) (\d+) (\d+) +(\d{4} . ...)( "(.*)")?$', line).groups()
            field_num = int(field_num)
            
            if field_num == 0: # New field list.
                if current_comp is not None:
                    raise Exception("Unexpected line '%s' inside component %s" % (line, current_comp))
                
                current_field_num = 0
                current_ref = field_value
                if field_value in components:
                    current_comp = components[field_value]
                    del components[field_value] # Remove this reference from the list of pending updates.
                
                new_sch += line + "\n"
            elif current_comp is None:
                # This field is not inside a component that we care about.
                new_sch += line + "\n"
                
                if field_num == 1:
                    if field_value in IGNORED_VALUES \
                    or current_ref.startswith('#PWR'):
                        pass # Ignore this component.
                    else:
                        untracked_references.add(current_ref)
            else:
                # Update the field value.
                
                if field_num < len(FIXED_FIELD_NAMES):
                    assert line_end is None
                    line_end = ''
                    field_name = FIXED_FIELD_NAMES[field_num]
                else:
                    field_name = field_name.strip()
                
                if field_name in current_comp:
                    current_field_num += 1
                    if field_num != current_field_num:
                        print("  Renumbering field %d to %d" % (field_num, current_field_num))
                    
		    if field_name == 'Datasheet':
                        flags = '0001 C CNN' #hide the field 
 
                    field_value = current_comp[field_name].strip()
                    del current_comp[field_name]
                    new_sch += 'F %s "%s" %s %s %s %s  %s%s\n' % (current_field_num, field_value, hori, posx, posy, size, flags, line_end)
                else:
                    untracked_fields.add(field_name)
                    # Remove untracked fields. This will mess field numbering, but KiCad will fix it next time.
                    # new_sch += line + "\n"
    
    untracked_references = untracked_references.difference(components_keys) # Avoid warning when two references are found for the same "split component" (op-amp, ...)
    if untracked_references:
        print("  %s untracked in csv" % ', '.join(untracked_references))
    return new_sch


def import_tsv_components(csv_file):
    print("Reading %s" % csv_file)
    
    # Read tsv
    components = {}
    with open(csv_file, 'r') as f :
        csvreader = csv.reader(f, delimiter='\t', quotechar='"')
        field_names = csvreader.next() # Read header
        field_names = [f.strip() for f in field_names]
        
        ref_index = field_names.index('Reference')
        
        for row in csvreader:
            # FIXME: check empty lines
            #~ print("  %s" % row[0])
            for cur_ref in re.split(', ?| ', row[ref_index]):
                cur_comp = {}
                for i, field_value in enumerate(row):
                    if field_names[i] not in IGNORED_COLUMNS:
                        cur_comp[field_names[i]] = field_value
                components[cur_ref] = cur_comp
    return components


if __name__ == '__main__' :
    if len(sys.argv) < 3:
        print("Usage: %s <tsv> <sch>...")
    else:
        components = import_tsv_components(sys.argv[1])
        
        new_fields = set()
        untracked_fields = set()
        diff_cmds = []
        for sch_file in sys.argv[2:]:
            # Update sch contents
            print("%s" % sch_file)
            sch = open(sch_file, 'r').read()
            new_sch = update_components(sch, components, new_fields, untracked_fields)
            
            # Overwrite file after backup
            bak = sch_file + '.bak'
            shutil.copyfile(sch_file, bak)
            with open(sch_file, 'w') as f:
                f.write(new_sch)
            
            diff_cmds.append("meld %-40s %s" % (bak, sch_file))
        
        #~ print("\nSee changes with:\n" + '\n'.join(diff_cmds))
        print("")
        print("New fields in csv : " + ', '.join(['"%s"' % s for s in new_fields]))
        print("Absent from csv   : " + ', '.join(['"%s"' % s for s in untracked_fields]))
        if components:
            print("These csv references were not found: %s" % ', '.join([k for k in components]))

