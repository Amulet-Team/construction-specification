# Construction Format Specification (Version 0)

All data is stored in big endian format. NBT strings are encoded in Java's modified utf-8 format.

The overall structure of the file is as follows:

| Name | Type | Description |
| :----: | :----: | ----------- |
| `construction header` | | [Construction Header](../../specifications#header-format)
| `section data table` | | [Section data table](section_data_table.md)
| `metadata` | TAG_Compound | [Metadata](metadata.md)
| `metadata start offset` | uint32 | offset from the start of the file to the start of the metadata entry
| `magic number` | `"constrct"` (8 bytes) UTF-8 char array | (Verifies that the file was saved correctly)

## Reading

1) Read the construction header to cofirm that it is a construction file with specification version 0
2) Skip to the end of the file and read the final `magic number`. If the value does not equal `constrct` the file is invalid (most likely only half saved)
3) Read the `metadata start offset` which will give you the offset to the start of `metadata`
4) Skip to the byte offset and read the [metadata](metadata.md) entry. This contains the offsets to each of the [section data entries](section_data_table.md#section-data-entry) in the section data table

## Writing

1) Write the construction header
2) Write each section data entry - keeping track of the locations where each exists in the file
3) Write the [metadata](metadata.md)
4) Write the offset to the start of the metadata
5) Write the magic number
