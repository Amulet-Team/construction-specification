# Construction Format Specification (Version 0)

    <magic number>: UTF-8 char array of value "constrct" (8 bytes)
    <format version>: byte - 0 for this version format
    <section data>: TAG_Compound - one or more sequential section entries
    <section data>: TAG_Compound
    <section data>: TAG_Compound
    ...
    <section table entry>: bytes
    <section table entry>: bytes
    <section table entry>: bytes
    ...
    <metadata>: TAG_Compound - data about the construction file
    <metadata start offset>: int - offset from the start of the file to the start of the metadata entry

## Section Data
Each section entry is a gzip'd TAG_Compound with the following structure:

    TAG_Compound({
        "entities": TAG_List([
            TAG_Compound({...}),
            TAG_Compound({...}),
            ...
        ]),
        "tile_entities": TAG_List([
            TAG_Compound({...}),
            TAG_Compound({...}),
            ...
        ]),
        "blocks_array_type": TAG_Byte(),
        "blocks": <See below>
    })

In order to reduce size of the construction format, the `blocks` array can either be a `TAG_Byte_Array`, a `TAG_Int_Array`,
or a `TAG_Long_Array` and the value of the `blocks_array_type` describes which of the two tag types was used by using their 
Tag ID, which can either be  7 (for TAG_Byte_Array) or 11 (for TAG_Int_Array) or 12 (for TAG_Long_Array)

### Blocks Array
The block array for each chunk is a flattened 16x16x16 array with each element being an index into the block palette.

### Entities and TileEntities
Entities and TileEntities are contained in a `TAG_List` with each element being a `TAG_Compound` of the entire NBT data associated with the given Entity/TileEntity

## Section Table
### Section Table Entry
Each section entry also has a corresponding entry in the section that includes information about the section, such as
lower bound coordinates of the section, the shape of the section, the starting byte position of the [section data](#Section Data) 
in the file, and the length of the corresponding section data.

This information is encoded in a sequence of bytes in little endian format of `<IIIBBBII` (where `I` denotes an unsigned 
integer and `B` for an unsigned char, see [Python Struct Docs](https://docs.python.org/3.8/library/struct.html#format-characters) 
for more information). This sequence of bytes represents the following information in this order:
- `III`: The X, Y, and Z coordinates of the section
- `BBB`: The shape of the section in X, Y, Z order
- `I`: The starting byte of the section data NBT in the file
- `I`: The length of the section data NBT

The total length of a single section table entry is 23 bytes.

## Metadata
The metadata for the construction is a gzip'd TAG_Compound laid out in the following format:

    TAG_Compound({
        "construction_shape": TAG_List([
            TAG_Int(<x>),
            TAG_Int(<y>),
            TAG_Int(<z>),
        ]),
        "minimum_structure_coordinates": TAG_List([
            TAG_Int(<min_x>),
            TAG_Int(<min_y>),
            TAG_Int(<min_z>),
        ])
        "section_table_position": TAG_Long(),
        "section_table_length": TAG_Long(),
        "block_palette": TAG_List([
            TAG_Compound(<block entry>),
            TAG_Compound(<block entry>),
            ...
        ]),
        "export_version": TAG_Compound({
            "edition": TAG_String().
            "version": TAG_List([
                TAG_Int(),
                TAG_Int(),
                TAG_Int()
            ])
        })
    })
    
### Construction Shape
The `construction_shape` tag is used to indicate the shape of the construction file. Each dimension is the number of 
sections present in that direction. So for example, a value of `[1, 2, 3]` indicates 1 section in the x direction, 2 
sections along the y direction, and 3 sections along the z direction.

### Minimum Structure Coordinates
Due to various NBT tags and elements of Minecraft (such as command blocks) relying on absolute coordinates, the 
construction includes a utility tag named `minimum_structure_coordinates` to mark the minimum coordinates for the start
of the construction. Since construction section coordinates are saved in relative coordinates, this allows for translation
back to absolute coordinates for anything that would require knowledge of the original absolute coordinates.

### Section Table Position
Stores the byte position where the [Section Table](#Section Table) begins in the file

### Section Table Length
Stores the length of the [Section Table](#Section Table) in bytes. Dividing this value by 23 (the byte length of a 
section entry) gives the total number of sections in the table (may be less than or equal to the product of the dimensions
from the [Construction Shape](#Construction Shape)) 

### Block Palette and Block Entry
The `block_palette` is a list of TAG_Compound's with each containing the data for one entry in the block palette. 
The layout for a palette entry is the following:

    TAG_Compound({
        "namespace": TAG_String("<block namespace>"),
        "blockname": TAG_String("<block base name>"),
        "properties": TAG_Compound({
            "<property_name>": TAG_String("<property value>"),
            "<property_name>": TAG_String("<property value>"),
            ...
        }),
        "extra_blocks": TAG_List([
            TAG_Int(<block palette index of the first extra block layer>),
            TAG_Int(<block palette index of the second extra block layer>),
            ...
        ])
    })

### Export Version
In order to properly indicate what format the Block Entries are in, the `export_version` tag describes the original 
version that the construction was export in. The `edition` tag describes the game edition the construction is from 
(IE: java, bedrock), and the `version` tag is a 3 element TAG_List that describes the full version number of the game in
the order of major number, minor number, patch number.