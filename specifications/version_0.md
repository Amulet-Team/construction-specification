# Construction Format Specification (Version 0)

    <magic number>: UTF-8 char array of value "constrct" (8 bytes)
    <format version>: byte - 0 for this version format
    <section entry>: TAG_Compound - one or more sequential section entries
    <section entry>: TAG_Compound
    <section entry>: TAG_Compound
    ...
    <metadata>: TAG_Compound - data about the construction file
    <metadata start offset>: int - offset from the start of the file to the start of the metadata entry

## Section Entry
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

## Metadata
The metadata for the construction is a gzip'd TAG_Compound laid out in the following format:

    TAG_Compound({
        "construction_shape": TAG_List([
            TAG_Int(<x>),
            TAG_Int(<y>),
            TAG_Int(<z>),
        ]),
        "index_table": TAG_Int_Array(),
        "block_palette": TAG_List([
            TAG_Compound(<block entry>),
            TAG_Compound(<block entry>),
            ...
        ]),
        "section_shape": TAG_List([
            TAG_Byte(),
            TAG_Byte(),
            TAG_Byte()
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
    
### Shape
The `construction_shape` tag is used to indicate the shape of the construction file. Each dimension is the number of 
sections present in that direction. So for example, a value of `[1, 2, 3]` indicates 1 section in the x direction, 2 
sections along the y direction, and 3 sections along the z direction.

### Section Index Table
The `index_table` is a flattened 3D int array in order XYZ with a shape described by the `construction_shape` that details
the offset that each section entry starts at. If the element value is 0, then the section does not exist and can be 
skipped, otherwise the section entry is located at that byte offset to the start of the file.

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

### Section Shape
The `section_shape` is a TAG_List that describes the expected shape of each section in the construction. Each
section of the construction will have a flattened `blocks` array that when reshaped should match the `section_shape`
dimensions. While different construction files can have different shape values, the section dimension shape should match
the shape described by the tag and be uniform across sections of a single construction file. 

### Export Version
In order to properly indicate what format the Block Entries are in, the `export_version` tag describes the original 
version that the construction was export in. The `edition` tag describes the game edition the construction is from 
(IE: java, bedrock), and the `version` tag is a 3 element TAG_List that describes the full version number of the game in
the order of major number, minor number, patch number.

## Boundary Section Behavior
If the uniform section shape would cause the said section to overflow outside of the desired export area, then the 
expected behavior of the application using the construction specification would be to ignore any blocks outside of the
"selection area" and set the value to -1 to mark that the block should be ignored.