# Section Data Table

The section data table is a sequence of zero or more [section data entries](section_data_table.md#section-data-entry) back to back in memory.

See [metadata](metadata.md) for how to know where each section is.

# Section Data Entry

A section data entry includes the data contained within a specified volume.

Each section data entry is a gzip'd binary TAG_Compound with the following structure:

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
The block array for each chunk is a flattened array of size specified in the [metadata section table](metadata.md#section-table) with each element being an index into the block palette.

### Entities and TileEntities
Entities and TileEntities are contained in a `TAG_List` with each element being a `TAG_Compound` of the entire NBT data associated with the given Entity/TileEntity
