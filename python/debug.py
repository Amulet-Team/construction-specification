"""Log some information about a specific construction file"""

import sys
from construction import ConstructionReader


def get_info(construction_file):
    with ConstructionReader(construction_file) as construction:
        print(f'Section count: {len(construction.sections)}')
        for i, selection in enumerate(construction.selection):
            print(f'Selection {i}, {selection}')
        for i, block in enumerate(construction.palette):
            print(f'Block {i}, {block}')
        for i, (posx, posy, posz, sizex, sizey, sizez, _, _) in enumerate(construction.sections):
            print(f'Section {i}, Pos:({posx}, {posy}, {posz}), Size:({sizex}, {sizey}, {sizez})')
            section = construction.read(i)
            print('\t', section.blocks)
            print('\t', section.entities)
            print('\t', section.block_entities)


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        print(arg)
        get_info(arg)
