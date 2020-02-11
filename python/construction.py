from __future__ import annotations

import functools
import io
import itertools
from math import log2, ceil
from typing import Tuple, Union, IO, Type

import struct

import numpy as np

from amulet.api import Block

import amulet_nbt as nbt

int_struct = struct.Struct("<I")


def find_fitting_array_type(
    array: np.ndarray
) -> Type[Union[nbt.TAG_Int_Array, nbt.TAG_Byte_Array, nbt.TAG_Long_Array]]:
    max_element = array.max()

    if max_element <= 127:
        return nbt.TAG_Byte_Array
    elif max_element <= 2_147_483_647:
        return nbt.TAG_Int_Array
    else:
        return nbt.TAG_Long_Array


def to_flattened_index(
    x: int, y: int, z: int, structure_size: Tuple[int, int, int]
) -> int:
    dx, dy, dz = structure_size
    return x * dy * dz + y * dz + z


def from_flattened_index(
    i: int, structure_size: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    dx, dy, dz = structure_size
    x = i // (dy * dz)
    y = (i // dz) % dy
    z = i % dz

    return x, y, z


class Construction:
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
            if not isinstance(other, Construction.ConstructionSection):
                return False
            return (
                self.sx == other.sx
                and self.sy == other.sy
                and self.sz == other.sz
                and np.equal(self.blocks, other.blocks).all()
                and self.entities == other.entities
                and self.tile_entities == other.tile_entities
            )

    def __init__(self, sections, block_palette, section_shape, source_edition_name: str, source_version: Tuple[int, int, int]):
        self.sections = sections
        self.block_palette = block_palette
        self.section_shape = section_shape
        self.source_edition = source_edition_name
        self.source_version = source_version

    def __eq__(self, other):
        if not isinstance(other, Construction):
            return False
        return (
            self.sections == other.sections
            and self.block_palette == other.block_palette
        )

    @classmethod
    def create_from(
        cls, iterable, palette, edition_name: str, edition_version: Tuple[int, int, int], section_shape: Tuple[int, int, int] = (16, 16, 16)
    ) -> Construction:
        sections = {}
        for section in iterable:
            if isinstance(section, cls.ConstructionSection):
                if section.blocks.shape != section_shape:
                    raise ValueError(
                        f"Section at {section.sx, section.sy, section.sz} does not have a shape of {section_shape}"
                    )
                sections[(section.sx, section.sy, section.sz)] = section
            else:
                sx, sy, sz = section.sx, section.sy, section.sz
                if section.blocks.shape != section_shape:
                    raise ValueError(
                        f"Section at {section.sx, section.sy, section.sz} does not have a shape of {section_shape}"
                    )
                sections[(sx, sy, sz)] = cls.ConstructionSection(
                    sx, sy, sz, section.blocks, section.entities, section.tile_entities
                )
        return cls(sections, palette, section_shape, edition_name, edition_version)

    def save(self, filename: str = None, buffer: IO = None):
        if filename is None and buffer is None:
            raise Exception()

        if filename is not None:
            buffer = open(filename, "wb+")

        def generate_section_entry(_section: Construction.ConstructionSection):
            if _section.blocks.shape != self.section_shape:
                raise ValueError(
                    f"Section at {_section.sx, _section.sy, _section.sz} does not have a shape of {self.section_shape}"
                )
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

        magic_num = "constrct".encode("utf-8")
        buffer.write(struct.pack(f"<{len(magic_num)}s", magic_num))
        buffer.write(struct.pack("<B", 0))

        section_map = {}
        for (sx, sy, sz), section_data in self.sections.items():
            position = buffer.tell()
            section_map[(sx, sy, sz)] = position
            section_buffer = io.BytesIO()
            generate_section_entry(section_data).save_to(
                filename_or_buffer=section_buffer, compressed=True
            )
            buffer.write(section_buffer.getvalue())

        sx_max = max(map(lambda s: s[0], section_map.keys()))
        sy_max = max(map(lambda s: s[1], section_map.keys()))
        sz_max = max(map(lambda s: s[2], section_map.keys()))

        structure_size = (sx_max + 1, sy_max + 1, sz_max + 1)

        coordinate_iter = itertools.product(
            range(sx_max + 1), range(sy_max + 1), range(sz_max + 1)
        )
        metadata = nbt.TAG_Compound(
            {
                "construction_shape": nbt.TAG_List([nbt.TAG_Int(v) for v in structure_size]),
                "section_shape": nbt.TAG_List(
                    [nbt.TAG_Byte(ceil(log2(v))) for v in self.section_shape]
                ),
                "export_version": nbt.TAG_Compound({
                    "edition": nbt.TAG_String(self.source_edition),
                    "version": nbt.TAG_List([
                        nbt.TAG_Int(v) for v in self.source_version
                    ])
                })
            }
        )

        index_table = [0] * functools.reduce(lambda v1, v2: v1 * v2, structure_size)
        for x, y, z in coordinate_iter:
            index_table[to_flattened_index(x, y, z, structure_size)] = section_map.get(
                (x, y, z), 0
            )

        metadata["index_table"] = nbt.TAG_Int_Array(index_table)

        extra_blocks = []
        for block in self.block_palette:
            palette = set(self.block_palette)
            if not all((eb in palette for eb in block.extra_blocks)):
                for eb in filter(lambda eb: eb not in palette, block.extra_blocks):
                    extra_blocks.append(eb)
        self.block_palette.extend(extra_blocks)

        block_palette_nbt = nbt.TAG_List()
        for block_entry in self.block_palette:
            block_entry_nbt = nbt.TAG_Compound(
                {
                    "namespace": nbt.TAG_String(block_entry.namespace),
                    "blockname": nbt.TAG_String(block_entry.base_name),
                    "properties": nbt.TAG_Compound(
                        {
                            prop: nbt.TAG_String(value)
                            for prop, value in block_entry.properties.items()
                        }
                    ),
                    "extra_blocks": nbt.TAG_List(
                        [
                            nbt.TAG_Int(self.block_palette.index(extra_block))
                            for extra_block in block_entry.extra_blocks
                        ]
                    ),
                }
            )
            block_palette_nbt.append(block_entry_nbt)

        metadata["block_palette"] = block_palette_nbt

        position = buffer.tell()
        metadata_buffer = io.BytesIO()
        nbt.NBTFile(metadata).save_to(
            filename_or_buffer=metadata_buffer, compressed=True
        )
        buffer.write(metadata_buffer.getvalue())
        buffer.write(int_struct.pack(position))

        buffer.close()

    @classmethod
    def load(cls, filename: str = None, buffer: IO = None, lazy_load: bool = True):

        if filename is not None:
            buffer = fp = open(filename, "rb")
            buffer = buffer.read()
            fp.close()

        magic_num = buffer[0:8].decode("utf-8")

        if magic_num != "constrct":
            raise AssertionError(
                f'Invalid magic number: expected: "constrct", got {magic_num}'
            )

        metadata_position = int_struct.unpack_from(
            buffer, len(buffer) - int_struct.size
        )[0]

        metadata = nbt.load(
            buffer=buffer[metadata_position : len(buffer) - int_struct.size],
            compressed=True,
        )

        try:
            edition_name = metadata["export_version"]["edition"].value
            edition_version = tuple(map(lambda v: v.value, metadata["export_version"]["version"]))
        except KeyError as e:
            raise AssertionError(f"Missing export version identifying key \"{e.args[0]}\"")


        block_palette = []
        extra_block_map = {}
        for block_index, block_nbt in enumerate(metadata["block_palette"]):
            block_namespace = block_nbt["namespace"].value
            block_basename = block_nbt["blockname"].value
            properties = {key: v.value for key, v in block_nbt["properties"].items()}
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

        structure_shape = tuple(map(lambda t: t.value, metadata["construction_shape"]))
        section_shape = tuple(map(lambda t: 2 ** t.value, metadata["section_shape"]))

        def section_iter():
            for i, index_value in enumerate(metadata["index_table"].value):
                if index_value == 0:
                    continue
                nbt_obj = nbt.load(
                    buffer=buffer[
                        index_value : buffer.index(
                            b"\037\213", index_value + 1
                        )  # \037\213 is the gzip magic constant
                    ],
                    compressed=True,
                )
                x, y, z = from_flattened_index(i, structure_shape)

                yield Construction.ConstructionSection(
                    x,
                    y,
                    z,
                    np.reshape(nbt_obj["blocks"].value, section_shape),
                    nbt_obj["entities"].value,
                    nbt_obj["tile_entities"].value,
                )

        return cls.create_from(
            section_iter(), block_palette, edition_name, edition_version, section_shape=section_shape
        )
