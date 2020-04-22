# Metadata
The metadata for the construction is a gzip'd TAG_Compound laid out in the following format:

    TAG_Compound({
        "selection_boxes": TAG_Int_Array([Nx6]),
        "section_index_table": TAG_Byte_Array([Mx23]),
        "section_version": TAG_Byte(),
        "export_version": TAG_Compound({
            "edition": TAG_String().
            "version": TAG_List([
                TAG_Int(),
                TAG_Int(),
                TAG_Int()
            ])
        })
        "block_palette": TAG_List([
            TAG_Compound(<block entry>),
            TAG_Compound(<block entry>),
            ...
        ]),
    })
    
## Selection Boxes
The `selection_boxes` tag is a TAG_Int_Array storing the coordinates of the areas that were selected in creating the construction file.

It consists of Nx6 ints where there are N boxes. The 6 ints for each box corrospond to the min_x, min_y, min_z, max_x, max_y and max_z respectively.

This is useful to display the areas that were selected when importing.

This data is required because a section that was selected can be missing if the data was not present when exporting.

## Section Index Table

The `section_index_table` is an Mx23 TAG_Byte_Array where M is the number of section data entries present in the construction file. May be empty if there are no section data entries.

The real format of the `section_index_table` is `IIIBBBII` where `I` is a uint32 and `B` is a uint8.

Each represents the following

- `III`: The X, Y, and Z block coordinates of the section
- `BBB`: The block shape of the section in X, Y, Z order
- `I`: The starting byte of the [section data entry](section_data_table.md#section-data-entry) in the file
- `I`: The byte length of the section data entry

## Section Version

This specifies the version number for the format of all the sections data entries contained in the [section data table](section_data_table.md#section-data-table). Currently the only valid value is 0 but this will enable modifying the format in the future.

## Export Version

All the game data contained within the construction file needs to be serialised to a specific versions format before saving.

This includes blocks, block entities and entities.

The `export_version` tag specifies the game `edition` (IE: `java`, `bedrock`) and game `version` number in
the order of major number, minor number, patch number.

## Block Palette
The `block_palette` is a list of TAG_Compound's with each containing the data for one entry in the block palette. 

### Block Entry

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
