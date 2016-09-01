#
# This script is a modified version of the one found in the sourcetree of KiCAD
#
"""
    @package
    Generate a BOM list file.
    Components are sorted by Footprint then Value
    One component per line
    Fields are (if exist)
    Reference, Footprint, Value, manf#, Datasheet
    Fields are separated by tabs
"""

from __future__ import print_function

# Import the KiCad python helper module and the csv formatter
import kicad_netlist_reader
import csv
import sys

# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
net = kicad_netlist_reader.netlist(sys.argv[1])

# Open a file to write to, if the file cannot be opened output to stdout
# instead
try:
    f = open(sys.argv[2], 'w')
except IOError:
    e = "Can't open output file for writing: " + sys.argv[2]
    print(__file__, ":", e, sys.stderr)
    f = sys.stdout

# Create a new csv writer object to use as the output formatter, although we
# are created a tab delimited list instead!
out = csv.writer(f, lineterminator='\n', delimiter='\t', quoting=csv.QUOTE_NONE)

# override csv.writer's writerow() to support utf8 encoding:
def writerow( acsvwriter, columns ):
    utf8row = []
    for col in columns:
        txt=str(col);
        utf8row.append( txt )
    acsvwriter.writerow( utf8row )

components = net.getInterestingComponents()

# Output a field delimited header line
writerow( out, ['Reference','Footprint', 'Value', 'manf#', 'Datasheet'] )

# Sort
components.sort(key=lambda item: item.getValue())
components.sort(key=lambda item: item.getFootprint())

# Output all of the component information
for c in components:
    writerow( out, [c.getRef(), c.getFootprint(), c.getValue(), 
                    c.getField("manf#"), c.getDatasheet(),])
