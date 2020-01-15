# Construction Format Specification (Version 0)

    <format version>: byte
    <block palette length>: int
    <block palette>: List[TAG_Compound]
    <entity/extra data>: TAG_Compound
    <chunk index table length>: int
    <chunk index table>: Tuple[<index>: int, <cx>: int, <cy>: int, <cz>: int]
    <chunk index marker>: int
    <chunk>: numpy.array
    <chunk index marker>: int
    <chunk>: numpy.array
    ...

## Block Palette 
The block palette is a list of Compound NBT tags with each containing the data for one entry in the block palette. The layout
for the palette entry is the following:
```
{
"namespace": TAG_String("<block namespace>"),
"blockname": TAG_String("<block base name>"),
"properties": TAG_Compound({
    "property_name": TAG_String("<property value>"),
    ...
}),
"extra_blocks": TAG_List([
    TAG_Int(<block palette index of the first extra block layer>),
    TAG_Int(<block palette index of the second extra block layer>),
    ...
])
}
```

## Entity/Extra Data
The entity/extra data section is for accommodating data such as TileEntities, Entities, TileTicks, etc. This is stored
as a Compound NBT Tag with the following structure:
```
{
"TileEntities": TAG_List([
    TAG_Compound({
        <NBT data>
    }),
    ...
]),
"Entities": TAG_List([
    TAG_Compound({
        <NBT data>
    }),
    ...
]),
"TileTicks": TAG_List([
    TAG_Compound({
        <NBT data>
    }),
    ...
]),
}
```

## Chunk Index Table
Continuous buffer of bytes detailing a chunk's (a chunk in this context is a 16x16x16 cube region) index 
(after the block palette) and it's corresponding chunk X, Y and Z coordinates (>= 0 values only). These values are 
packed as a C Struct with the struct format of `<IIII` (4 unsigned ints), and are ordered as (index, chunk X coordinate, chunk Y coordinate, chunk Z coordinate)

## Chunk Data Entry
A sequence of serialized chunk data, with the start of each new chunk section being marked with a integer index to pair 
the chunk data with the entry from the [Chunk Index Table](#Chunk Index Table). 

### Chunk Entry Header
As of 07.01.2020, this is a sequence of bytes
in the form `<IBH` (1 unsigned int, 1 unsigned byte, and 1 unsigned short) where the integer value denotes the chunk index this entry
belongs to, the byte indicates the amount of bytes used for each entry in the array, and the short is used for the flattened length of the block array.
The following possible values for the amount of bytes each element can be are: 1 (unsigned byte), 2 (unsigned short), 4 (unsigned int)

### Chunk Block Array
The block array for each chunk is a flattened 16x16x16 array with each element being comprosed of the amount of bytes indicated in the chunk's entry header.
Each element within this array is an index into the block palette.
