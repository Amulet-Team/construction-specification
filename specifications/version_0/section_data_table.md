# Section Data Table

The section data table is a sequence of zero or more [section data entries](section_data_table.md#section-data-entry) back to back in memory.

See [metadata's section index table](metadata.md#section-index-table) for how to know where each section is.

# Section Data Entry

A section data entry includes the data contained within a specified volume.

Each volume must fit within a single sub-chunk where a sub-chunk is a 16x16x16 region of blocks with the first alligned with 0,0,0. This means that a section can be at most 16x16x16 blocks however it can be smaller by modifying the minimum coordinates and/or the section shape.

There can be multiple sections per sub-chunk.

Each section data entry is a gzip'd binary TAG_Compound with the following structure:

    TAG_Compound({
        "entities": TAG_List([
            TAG_Compound({
                "namespace": TAG_String(),
                "base_name": TAG_String(),
                "x": TAG_Double(),
                "y": TAG_Double(),
                "z": TAG_Double(),
                "nbt": TAG_Compound()
            })
            ...
        ]),
        "block_entities": TAG_List([
            TAG_Compound({
                "namespace": TAG_String(),
                "base_name": TAG_String(),
                "x": TAG_Int(),
                "y": TAG_Int(),
                "z": TAG_Int(),
                "nbt": TAG_Compound()
            })
            ...
        ]),
        "blocks_array_type": TAG_Byte(),
        "blocks": <See below>
    })

In order to reduce size of the construction format, the `blocks` array can either be a `TAG_Byte_Array`, a `TAG_Int_Array`,
or a `TAG_Long_Array` and the value of the `blocks_array_type` describes which of the two tag types was used by using their 
Tag ID, which can either be  7 (for TAG_Byte_Array) or 11 (for TAG_Int_Array) or 12 (for TAG_Long_Array)

There is also a special case where this tag equals -1 which means that the `blocks` and `block_entities` tag do not exist. This is useful for storing sections that contain entities but are not populated with block data.

### Blocks Array
The block array for each chunk is a flattened array of size specified in the [metadata section index table](metadata.md#section-index-table) with each element being an index into the [block palette](metadata.md#block-palette).

### Entities and BlockEntities
Entities and BlockEntities are contained in a `TAG_List` with each element being a `TAG_Compound` in the format as shown above. They are converted into the format for the version specified in the [metadata](metadata.md#export-version) before they are serialised.
