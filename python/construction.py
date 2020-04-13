from __future__ import annotations

import io
import itertools
import os
import struct
from typing import Type, Union, Tuple, IO, Dict

from amulet import Block

import amulet_nbt as nbt

import numpy as np

INT_STRUCT = struct.Struct("<I")
SECTION_ENTRY_STRUCT = struct.Struct("<IIIBBBII")
print(SECTION_ENTRY_STRUCT.size)


def find_fitting_array_type(
    array: np.ndarray
) -> Type[Union[nbt.TAG_Int_Array, nbt.TAG_Byte_Array, nbt.TAG_Long_Array]]:
    max_element = array.max(0)

    if max_element <= 127:
        return nbt.TAG_Byte_Array
    elif max_element <= 2_147_483_647:
        return nbt.TAG_Int_Array
    else:
        return nbt.TAG_Long_Array


class ConstructionSection:
    __slots__ = ("sx", "sy", "sz", "blocks", "entities", "tile_entities")

    def __init__(
        self,
        sx: int,
        sy: int,
        sz: int,
        blocks: np.ndarray,
        entities: list,
        tile_entities: list,
    ):
        self.sx = sx
        self.sy = sy
        self.sz = sz
        self.blocks = blocks
        self.entities = entities
        self.tile_entities = tile_entities

    def __eq__(self, other):
        if not isinstance(other, ConstructionSection):
            return False
        return (
            self.sx == other.sx
            and self.sy == other.sy
            and self.sz == other.sz
            and np.equal(self.blocks, other.blocks).all()
            and self.entities == other.entities
            and self.tile_entities == other.tile_entities
        )


class Construction:
    def __init__(
        self,
        sections: Dict[Tuple[int, int, int], ConstructionSection],
        palette,
        source_edition: str,
        source_version: Tuple[int, int, int],
    ):
        self.sections = sections
        self.palette = palette
        self.source_edition = source_edition
        self.source_version = source_version

    def __eq__(self, other):
        if not isinstance(other, Construction):
            return False
        return (
            self.sections == other.sections
            and self.source_edition == other.source_edition
            and self.source_version == other.source_version
        )

    @classmethod
    def create_from(
        cls, iterable, palette, edition_name, edition_version
    ) -> Construction:
        sections = {}
        for section in iterable:
            section_coords = (section.sx, section.sy, section.sz)
            sections[section_coords] = ConstructionSection(
                *section_coords, section.blocks, section.entities, section.tile_entities
            )

        return cls(sections, palette, edition_name, edition_version)

    def save(self, filename: str = None, buffer: IO = None):
        if filename is None and buffer is None:
            raise Exception()

        if filename is not None:
            buffer = open(filename, "wb+")

        def generate_section_entry(_section: ConstructionSection) -> nbt.NBTFile:
            flattened_array = _section.blocks.ravel()
            array_type = find_fitting_array_type(flattened_array)
            _tag = nbt.TAG_Compound(
                {
                    "entities": nbt.TAG_List(_section.entities),
                    "tile_entities": nbt.TAG_List(_section.tile_entities),
                    "blocks": array_type(flattened_array),
                    "blocks_array_type": nbt.TAG_Byte(array_type().tag_id),
                }
            )
            return nbt.NBTFile(_tag)

        def generate_block_entry(
            _block: Block, _palette_len, _extra_blocks
        ) -> nbt.TAG_Compound:
            return nbt.TAG_Compound(
                {
                    "namespace": nbt.TAG_String(_block.namespace),
                    "blockname": nbt.TAG_String(_block.base_name),
                    "properties": nbt.TAG_Compound(
                        {
                            prop: nbt.TAG_String(value.value)
                            for prop, value in _block.properties.items()
                        }
                    ),
                    "extra_blocks": nbt.TAG_List(
                        [
                            nbt.TAG_Int(
                                _palette_len + _extra_blocks.index(_extra_block)
                            )
                            for _extra_block in _block.extra_blocks
                        ]
                    ),
                }
            )

        magic_num = "constrct".encode("utf-8")
        buffer.write(struct.pack(f"<{len(magic_num)}s", magic_num))
        buffer.write(struct.pack("<B", 0))

        section_map = {}
        for section_coords, section_data in self.sections.items():
            buffer_position = buffer.tell()
            section_buffer = io.BytesIO()
            generate_section_entry(section_data).save_to(
                filename_or_buffer=section_buffer, compressed=True
            )
            buffer.write(section_buffer.getvalue())
            section_map[section_coords] = (
                buffer_position,
                buffer.tell() - buffer_position,
            )

        sx_max = max(map(lambda s: s[0], section_map.keys()))
        sy_max = max(map(lambda s: s[1], section_map.keys()))
        sz_max = max(map(lambda s: s[2], section_map.keys()))

        sx_min = min(map(lambda s: s[0], section_map.keys()))
        sy_min = min(map(lambda s: s[1], section_map.keys()))
        sz_min = min(map(lambda s: s[2], section_map.keys()))

        min_structure_coords = (sx_min, sy_min, sz_min)
        structure_size = (
            (sx_max - sx_min) + 1,
            (sy_max - sy_min) + 1,
            (sz_max - sz_min) + 1,
        )

        metadata = nbt.TAG_Compound(
            {
                "construction_shape": nbt.TAG_List(
                    [nbt.TAG_Int(v) for v in structure_size]
                ),
                "minimum_structure_coordinates": nbt.TAG_List(
                    [nbt.TAG_Int(v) for v in min_structure_coords]
                ),
                "export_version": nbt.TAG_Compound(
                    {
                        "edition": nbt.TAG_String(self.source_edition),
                        "version": nbt.TAG_List(
                            [nbt.TAG_Int(v) for v in self.source_version]
                        ),
                    }
                ),
            }
        )

        section_table_position = buffer.tell()
        metadata["section_table_position"] = nbt.TAG_Long(section_table_position)

        section_table_length = 0
        coordinate_iter = itertools.product(*map(range, structure_size))
        for coordinates in coordinate_iter:
            adjusted_coordinates = (
                sx_min + coordinates[0],
                sy_min + coordinates[1],
                sz_min + coordinates[2],
            )

            if adjusted_coordinates in self.sections:
                section = self.sections[adjusted_coordinates]

                buffer.write(
                    SECTION_ENTRY_STRUCT.pack(
                        *coordinates,
                        *section.blocks.shape,
                        *section_map[adjusted_coordinates],
                    )
                )
                section_table_length += 1
        metadata["section_table_length"] = nbt.TAG_Long(
            section_table_length * SECTION_ENTRY_STRUCT.size
        )

        block_palette_nbt = nbt.TAG_List()
        extra_blocks = set()

        for block in self.palette:
            if len(block.extra_blocks) > 0:
                extra_blocks.update(block.extra_blocks)

        extra_blocks = list(extra_blocks)

        palette_len = len(self.palette)
        for block_entry in self.palette:
            block_palette_nbt.append(
                generate_block_entry(block_entry, palette_len, extra_blocks)
            )

        for extra_block in extra_blocks:
            block_palette_nbt.append(
                generate_block_entry(extra_block, palette_len, extra_blocks)
            )

        metadata["block_palette"] = block_palette_nbt

        position = buffer.tell()
        metadata_buffer = io.BytesIO()
        nbt.NBTFile(metadata).save_to(
            filename_or_buffer=metadata_buffer, compressed=True
        )
        buffer.write(metadata_buffer.getvalue())
        buffer.write(INT_STRUCT.pack(position))

        buffer.close()

    @classmethod
    def load(cls, filename: str = None, buffer: IO = None, load_as_relative=True) -> Construction:

        if filename is not None:
            buffer = open(filename, "rb")

        magic_num = buffer.read(8).decode("utf-8")

        if magic_num != "constrct":
            raise AssertionError(
                f'Invalid magic number: expected: "constrct", got {magic_num}'
            )

        buffer.seek(0, os.SEEK_END)
        buffer_size = buffer.tell()
        buffer.seek(buffer_size - INT_STRUCT.size)
        metadata_position = INT_STRUCT.unpack(buffer.read(INT_STRUCT.size))[0]

        buffer.seek(metadata_position)

        metadata = nbt.load(
            buffer=buffer.read(buffer_size - (metadata_position + INT_STRUCT.size)),
            compressed=True,
        )

        try:
            edition_name = metadata["export_version"]["edition"].value
            edition_version = tuple(
                map(lambda v: v.value, metadata["export_version"]["version"])
            )
        except KeyError as e:
            raise AssertionError(
                f'Missing export version identifying key "{e.args[0]}"'
            )

        block_palette = []
        extra_block_map = {}
        for block_index, block_nbt in enumerate(metadata["block_palette"]):
            block_namespace = block_nbt["namespace"].value
            block_basename = block_nbt["blockname"].value
            properties = {key: v for key, v in block_nbt["properties"].items()}
            block = Block(
                namespace=block_namespace,
                base_name=block_basename,
                properties=properties,
            )

            if block_nbt["extra_blocks"].value:
                extra_block_map[block_index] = block_nbt["extra_blocks"].value

            block_palette.append(block)

        for block_index, extra_blocks in extra_block_map.items():
            extra_block_objects = [block_palette[i.value] for i in extra_blocks]

            resulting_block = block_palette[block_index]
            for extra_block in extra_block_objects:
                resulting_block = resulting_block + extra_block

            block_palette[block_index] = resulting_block

        min_sections_coords = tuple(
            map(lambda t: t.value, metadata["minimum_structure_coordinates"])
        )
        section_table_position = metadata["section_table_position"].value
        section_table_length = metadata["section_table_length"].value

        def section_iter():
            for i in range(section_table_length // SECTION_ENTRY_STRUCT.size):
                entry_index = section_table_position + (
                    i * SECTION_ENTRY_STRUCT.size
                )
                buffer.seek(entry_index)
                sx, sy, sz, shapex, shapey, shapez, position, length = SECTION_ENTRY_STRUCT.unpack(
                    buffer.read(SECTION_ENTRY_STRUCT.size)
                )

                buffer.seek(position)

                nbt_obj = nbt.load(buffer=buffer.read(length), compressed=True)

                yield ConstructionSection(
                    sx if load_as_relative else min_sections_coords[0] + sx,
                    sy if load_as_relative else min_sections_coords[1] + sy,
                    sz if load_as_relative else min_sections_coords[2] + sz,
                    np.reshape(nbt_obj["blocks"].value, (shapex, shapey, shapez)),
                    nbt_obj["entities"].value,
                    nbt_obj["tile_entities"].value,
                )
            buffer.close()

        return cls.create_from(
            section_iter(), block_palette, edition_name, edition_version
        )
