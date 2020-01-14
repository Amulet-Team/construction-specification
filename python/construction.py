from __future__ import annotations

import itertools
from typing import List, Tuple, Dict, Union, Iterator, IO, Mapping

import struct

import numpy as np

from amulet.api import Block

import amulet_nbt as nbt

version_struct = struct.Struct("<B")

chunk_index_struct = struct.Struct("<4I")
CHUNK_INDEX_SIZE = chunk_index_struct.size

int_struct = struct.Struct("<I")

DT = np.dtype(int)

size_map = {
    struct.calcsize("<B"): struct.Struct("<B"),
    struct.calcsize("<H"): struct.Struct("<H"),
    struct.calcsize("<I"): struct.Struct("<I"),
}


def find_fitting_struct(array: np.ndarray) -> struct.Struct:
    max_element_value = array.max()
    for struct_size, struct_obj in size_map.items():
        max_supported_value = (2 ** (8 * struct_size)) - 1
        if max_element_value <= max_supported_value:
            return struct_obj
    return struct.Struct("<I")


class Construction:
    class ConstructionSubSection:
        __slots__ = ("cx", "cy", "cz", "blocks")

        def __init__(self, cx: int, cy: int, cz: int, blocks: np.ndarray):
            self.cx, self.cy, self.cz = cx, cy, cz
            self.blocks = blocks

        def __repr__(self):
            return f"_ConstructionSubChunk(cx={self.cx}, cy={self.cy} cz={self.cz}, blocks={self.blocks})"

        def __eq__(self, other: "Construction.ConstructionSubSection") -> bool:
            if other is None:
                return False
            return (
                self.cx == other.cx
                and self.cy == other.cy
                and self.cz == other.cz
                and np.equal(self.blocks, other.blocks).all()
            )

        def __getattr__(self, item):
            return getattr(self.blocks, item)

    def __init__(
        self,
        chunk_sections: "Dict[Tuple[int, int, int], ConstructionSubSection]",
        block_palette: "List[Block]",
        extra_data: nbt.TAG_Compound,
    ):
        self.chunk_sections = chunk_sections
        self.block_palette = block_palette
        self.extra_data = extra_data

    @property
    def sections(self):
        yield from self.chunk_sections

    def __eq__(self, other: Construction) -> bool:
        if not other:
            return False
        return (
            self.chunk_sections == other.chunk_sections
            and self.block_palette == other.block_palette
        )

    def save(self, filename: str = None, buffer: IO = None) -> None:
        if filename is None and buffer is None:
            raise Exception()

        if filename is not None:
            buffer = open(filename, "wb")

        buffer.write(
            version_struct.pack(1)
        )  # Unsigned char at beginning of file for format version

        extra_blocks = []
        for block in self.block_palette:
            palette = set(self.block_palette)
            if not all((eb in palette for eb in block.extra_blocks)):
                for eb in filter(lambda eb: eb not in palette, block.extra_blocks):
                    extra_blocks.append(eb)

        self.block_palette.extend(extra_blocks)

        buffer.write(int_struct.pack(len(self.block_palette)))

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
            block_entry_nbt.save(buffer)

        extra_data = nbt.TAG_Compound(
            {
                "Entities": nbt.TAG_List(),
                "TileEntities": nbt.TAG_List(),
                "TileTicks": nbt.TAG_List(),
            }
        )

        extra_data.save(buffer)

        buffer.write(int_struct.pack(len(self.chunk_sections) * CHUNK_INDEX_SIZE))

        for i, chunk in enumerate(self.chunk_sections.values()):
            buffer.write(chunk_index_struct.pack(i, chunk.cx, chunk.cy, chunk.cz))

        for i, chunk in enumerate(self.chunk_sections.values()):
            blocks_array: np.ndarray = chunk.blocks.copy().ravel()
            struct_to_use = find_fitting_struct(blocks_array)
            buffer.write(struct.pack("<IBH", i, struct_to_use.size, len(blocks_array)))
            for element in blocks_array:
                buffer.write(struct_to_use.pack(element))

        buffer.close()

    @classmethod
    def create_from(
        cls, iterator: Iterator, block_palette: List[Block], extra_data: Mapping
    ) -> Construction:
        chunks = {}
        for section in iterator:
            if isinstance(section, cls.ConstructionSubSection):
                chunks[(section.cx, section.cy, section.cz)] = section
            else:
                cx, cy, cz = section.cx, section.cy, section.cz
                chunks[(cx, cy, cz)] = cls.ConstructionSubSection(
                    cx, cy, cz, section.blocks
                )

        return Construction(chunks, block_palette, extra_data)

    @classmethod
    def load(
        cls, filename: str = None, buffer: IO = None, lazy_load: bool = True
    ) -> Construction:
        if filename is not None:
            buffer = fp = open(filename, "rb")
            buffer = buffer.read()
            fp.close()

        offset = 0

        def read_from_struct(buf: IO, _struct: "Union[struct.Struct, str]"):
            nonlocal offset
            if isinstance(_struct, struct.Struct):
                _value = _struct.unpack_from(buf, offset)
                offset += _struct.size
            else:
                _value = struct.unpack_from(_struct, buf, offset)
                offset += struct.calcsize(_struct)
            return _value

        version_id = read_from_struct(buffer, version_struct)[0]

        block_palette_length = read_from_struct(buffer, int_struct)[0]

        block_palette = []
        extra_block_map = {}
        block_data, new_offset = nbt.load(
            buffer=buffer[offset:],
            compressed=False,
            count=block_palette_length,
            offset=True,
        )
        for block_index, block_nbt in enumerate(block_data):
            block_namespce = block_nbt["namespace"].value
            block_base_name = block_nbt["blockname"].value
            properties = {key: v.value for key, v in block_nbt["properties"].items()}
            block = Block(
                namespace=block_namespce,
                base_name=block_base_name,
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

        offset += new_offset

        extra_data, new_offset = nbt.load(
            buffer=buffer[offset:], compressed=False, offset=True
        )
        offset += new_offset

        chunk_table_length = read_from_struct(buffer, int_struct)[0]

        number_of_chunks = chunk_table_length // CHUNK_INDEX_SIZE
        chunks = {}
        for i in range(number_of_chunks):
            chunk_index, cx, cy, cz = read_from_struct(buffer, chunk_index_struct)
            chunks[chunk_index] = {"chunk_coords": (cx, cy, cz), "blocks": None}

        if lazy_load:

            def chunk_iter(
                _buffer: IO, _number_of_chunks: int
            ) -> Iterator[Construction.ConstructionSubSection]:
                # More efficient since iterator value isn't changed, initialized, or used with each iteration
                for _ in itertools.repeat(None, times=_number_of_chunks):
                    owning_chunk, element_struct_size, array_len = read_from_struct(
                        _buffer, "<IBH"
                    )
                    element_struct = size_map[element_struct_size]

                    blocks_array = np.zeros(array_len, dtype=DT)
                    for i in range(array_len):
                        blocks_array[i] = read_from_struct(_buffer, element_struct)[0]
                    blocks_array = blocks_array.reshape((16, 16, 16))
                    yield cls.ConstructionSubSection(
                        *chunks[owning_chunk]["chunk_coords"], blocks_array
                    )

        else:
            # More efficient since iterator value isn't changed, initialized, or used with each iteration
            for _ in itertools.repeat(None, times=number_of_chunks):
                owning_chunk, element_struct_size, array_len = read_from_struct(
                    buffer, "<IBH"
                )
                struct_to_use = size_map[element_struct_size]

                blocks_array = np.zeros(array_len, dtype=DT)
                for i in range(array_len):
                    blocks_array[i] = read_from_struct(buffer, struct_to_use)[0]
                chunks[owning_chunk]["blocks"] = blocks_array

            created_chunks = []
            for chunk_data in chunks.values():
                cx, cy, cz = chunk_data["chunk_coords"]

                if chunk_data["blocks"] is None:
                    blocks = np.zeros((16, 16, 16), dtype=np.uint16)
                else:
                    blocks = chunk_data["blocks"].reshape((16, 16, 16))
                created_chunks.append(cls.ConstructionSubSection(cx, cy, cz, blocks))

            def chunk_iter(
                _1, _2
            ) -> Iterator[
                Construction.ConstructionSubSection
            ]:  # Mimic the arguments of the lazy loader and discard them
                yield from created_chunks

        return cls.create_from(
            chunk_iter(buffer, number_of_chunks), block_palette, extra_data
        )
