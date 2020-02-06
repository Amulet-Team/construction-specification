# Construction Format Specification (Version 0)

    <magic number>: UTF-8 char array of value "constrct" (8 bytes)
    <format version>: byte
    <section entry>: TAG_Compound
    <section entry>: TAG_Compound
    <section entry>: TAG_Compound
    ...
    <metadata>: TAG_Compound
    <metadata start offset>: int

## Section Entry
Each section entry is a gzip'd TAG_Compound with the following structure:

    TAG_Compound({
        "Entities": TAG_List([
            TAG_Compound({...}),
            TAG_Compound({...}),
            ...
        ]),
        "TileEntities": TAG_List([
            TAG_Compound({...}),
            TAG_Compound({...}),
            ...
        ]),
        "BlocksArrayType": TAG_Byte(),
        "Blocks": <See below>
    })

In order to reduce size of the construction format, the `Blocks` array can either be a `TAG_Byte_Array`, a `TAG_Int_Array`,
or a `TAG_Long_Array` and the value of the `BlocksArrayType` describes which of the two tag types was used by using their 
Tag ID, which can either be  7 (for TAG_Byte_Array) or 11 (for TAG_Int_Array) or 12 (for TAG_Long_Array)

### Blocks Array
The block array for each chunk is a flattened 16x16x16 array with each element being an index into the block palette.

### Entities and TileEntities
Entities and TileEntities are contained in a `TAG_List` with each element being a `TAG_Compound` of the entire NBT data associated with the given Entity/TileEntity

## Metadata
The metadata for the construction is a gzip'd TAG_Compound laid out in the following format:

    TAG_Compound({
        "shape": TAG_List([
            TAG_Int(<x>),
            TAG_Int(<y>),
            TAG_Int(<z>),
        ]),
        "index_table": TAG_Int_Array(),
        "block_palette": TAG_List([
            TAG_Compound(<block entry>),
            TAG_Compound(<block entry>),
            ...
        ])
    })
    
### Shape
The `shape` tag is used to indicate the number of sections in each of the 3 directions.

### Section Index Table
The `index_table` is an int array that details the offset that each section entry starts at.
If the element value is 0, then the section does not exist and can be skipped, otherwise the element value is the 
offset location of the given section. The indexes of the array map to the X,Y,Z coordinates of the corresponding section
and can be calculated to and from their flattened index using the functions described below:
```python
def to_flattened_index(x: int, y: int, z: int, structure_size: Tuple[int, int, int]) -> int:
    dx, dy, dz = structure_size
    return x * dy * dz + y * dz + z


def from_flattened_index(i: int, structure_size: Tuple[int, int, int]) -> Tuple[int, int, int]:
    dx, dy, dz = structure_size
    x = i // (dy * dz)
    y = (i // dz) % dy
    z = i % dz

    return x, y, z
```

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

