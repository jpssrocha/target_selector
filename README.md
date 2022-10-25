# Target Selection Tool

This software is a simple target selection tool to select targets (variable
stars or stellar clusters) based on it's position on the sky, the observatory
location, and some filters. 

It will print a catalog with the best targets to observe along with some info
and a formatted list that's easy to use with this another tool:

http://catserver.ing.iac.es/staralt/

## Installation

To install it in a conda environment with conda use:

$ conda install --file requirements.txt

## Basic Usage

1. Activate the conda environment
2. Enter the script folder
3. Run it with `$python target_selector.py`
4. Input the required info

## Known bugs

### Start and end of the night selections can get exchanged

This is a simple script script, therefore does not contain safe guards to take
into consideration the cyclical nature of this task (that 24h = 0h). So
sometimes this will make the script give targets on the first half of the night
when asked for targets on the second half and vice versa.

> **Therefore ALWAYS CHECK with the visibility plot**

### Output columns getting mixed up

This happens when the terminal font is too large for the table to be rendered
on the available columns.

Is this case simply decrease the font size and run again.

## References

- Cantat-Gaudin+, 2020 -> For a catalog of open clusters
- Samus+, 2017 -> For a catalog of field variable stars (GCVS 5.1)
- ESA, 1997, The Hipparcos and Tycho Catalogues, ESA SP-1200 -> For neighbor checking
