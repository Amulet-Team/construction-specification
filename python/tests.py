from __future__ import annotations
import unittest
import glob
import os

import numpy

from amulet.api import Block

from .construction import Construction

REMOVE_TEST_GENERATED_FILES = True


class MockedChunk:
    def __init__(self, cx, cy, cz, blocks):
        self.cx = cx
        self.cy = cy
        self.cz = cz
        self.blocks = blocks


class ConstructionTestCase(unittest.TestCase):
    small_block_palette = [
        Block("minecraft:air"),
        Block("minecraft:stone"),
        Block("minecraft:oak_planks"),
        Block("minecraft:diamond_block"),
        Block("minecraft:dirt"),
        Block("minecraft:lime_concrete"),
        Block("minecraft:orange_concrete"),
        Block("minecraft:quartz_block"),
        Block("minecraft:sandstone"),
    ]

    def tearDown(self) -> None:
        if not REMOVE_TEST_GENERATED_FILES:
            return
        files_to_remove = glob.iglob("*.construction")
        for f in files_to_remove:
            os.remove(f)

    def test_construction_creation_1(self):

        block_layout = numpy.zeros((16, 16, 16), dtype=int)
        block_layout[0:8, 0:8, 0:8] = 1
        block_layout[0:8, 0:8, 8:16] = 2
        block_layout[0:8, 8:16, 0:8] = 3
        block_layout[0:8, 8:16, 8:16] = 4
        block_layout[8:16, 0:8, 0:8] = 5
        block_layout[8:16, 0:8, 8:16] = 6
        block_layout[8:16, 8:16, 0:8] = 7
        block_layout[8:16, 8:16, 8:16] = 8

        mocked_chunk = MockedChunk(0, 0, 0, block_layout)

        def _iter():
            yield mocked_chunk

        construction_obj_1 = Construction.create_from(
            _iter(), self.small_block_palette, {}
        )
        # Since the mocked chunk object has the same attribute names as the internal section object of Construction
        # objects we can just directly compare them to see if it was properly added to the construction
        self.assertEqual(construction_obj_1.chunk_sections[(0, 0, 0)], mocked_chunk)
        construction_obj_1.save("test_construction_creation_1.construction")

        construction_obj_2 = Construction.load(
            "test_construction_creation_1.construction"
        )
        self.assertEqual(construction_obj_2.chunk_sections[(0, 0, 0)], mocked_chunk)
        self.assertEqual(construction_obj_1, construction_obj_2)


if __name__ == "__main__":
    unittest.main()
