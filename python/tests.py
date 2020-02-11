from __future__ import annotations

import time
import unittest
import glob
import os
from itertools import product

import numpy as np

from amulet.api import Block

from .construction import Construction

REMOVE_TEST_GENERATED_FILES = True
RUN_STRESS_TEST = False

TEST_EDITION = 'java'
TEST_VERSION = (1, 13, 2)

class MockedChunk:
    def __init__(self, sx, sy, sz, blocks, entities, tile_entities):
        self.sx = sx
        self.sy = sy
        self.sz = sz
        self.blocks = blocks
        self.entities = entities
        self.tile_entities = tile_entities

    def __eq__(self, other):
        return (
            self.sx == other.sx
            and self.sy == other.sy
            and self.sz == other.sz
            and np.equal(self.blocks, other.blocks).all()
            and self.entities == other.entities
            and self.tile_entities == other.tile_entities
        )


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
        Block(
            "minecraft:stone",
            extra_blocks=Block("minecraft:damaged_anvil[facing=south]"),
        ),
    ]

    def tearDown(self) -> None:
        if not REMOVE_TEST_GENERATED_FILES:
            return
        files_to_remove = glob.iglob("*.construction")
        for f in files_to_remove:
            os.remove(f)

    def test_non_cube_sections(self):

        block_layout = np.zeros((8, 16, 8), dtype=int)
        block_layout[0:8, 0:8, 0:8] = 1
        block_layout[8:16, 8:16, 8:16] = 8

        mocked_section = MockedChunk(0, 0, 0, block_layout, [], [])

        def _iter():
            yield mocked_section

        construct_1 = Construction.create_from(_iter(), self.small_block_palette, TEST_EDITION, TEST_VERSION, section_shape=(8, 16, 8))
        self.assertEqual(mocked_section, construct_1.sections[(0, 0, 0)])
        construct_1.save("test_non_cube_sections.construction")

        construct_2 = Construction.load("test_non_cube_sections.construction")
        self.assertEqual(mocked_section, construct_2.sections[(0, 0, 0)])
        self.assertEqual(construct_1, construct_2)



    def test_construction_creation_1(self):

        block_layout = np.zeros((16, 16, 16), dtype=int)
        block_layout[0:8, 0:8, 0:8] = 1
        block_layout[0:8, 0:8, 8:16] = 2
        block_layout[0:8, 8:16, 0:8] = 3
        block_layout[0:8, 8:16, 8:16] = 4
        block_layout[8:16, 0:8, 0:8] = 5
        block_layout[8:16, 0:8, 8:16] = 6
        block_layout[8:16, 8:16, 0:8] = 7
        block_layout[8:16, 8:16, 8:16] = 8

        mocked_chunk = MockedChunk(0, 0, 0, block_layout, [], [])

        def _iter():
            yield mocked_chunk

        construction_obj_1 = Construction.create_from(_iter(), self.small_block_palette, TEST_EDITION, TEST_VERSION)
        # Since the mocked chunk object has the same attribute names as the internal section object of Construction
        # objects we can just directly compare them to see if it was properly added to the construction
        self.assertEqual(mocked_chunk, construction_obj_1.sections[(0, 0, 0)])
        construction_obj_1.save("test_construction_creation_1.construction")

        construction_obj_2 = Construction.load(
            "test_construction_creation_1.construction"
        )
        self.assertEqual(mocked_chunk, construction_obj_2.sections[(0, 0, 0)])
        self.assertEqual(construction_obj_1, construction_obj_2)

    @unittest.skipUnless(RUN_STRESS_TEST, "Stress tests not enabled")
    def test_construction_creation_2(self):
        block_layout = np.zeros((16, 16, 16), dtype=int)
        block_layout[0:8, 0:8, 0:8] = 1
        block_layout[0:8, 0:8, 8:16] = 2
        block_layout[0:8, 8:16, 0:8] = 3
        block_layout[0:8, 8:16, 8:16] = 4
        block_layout[8:16, 0:8, 0:8] = 5
        block_layout[8:16, 0:8, 8:16] = 6
        block_layout[8:16, 8:16, 0:8] = 7
        block_layout[8:16, 8:16, 8:16] = 8

        def _iter():
            for x, y, z in product(range(50), range(50), range(50)):
                yield MockedChunk(x, y, z, block_layout, [], [])

        construction_obj_1 = Construction.create_from(_iter(), self.small_block_palette, TEST_EDITION, TEST_VERSION)
        # Since the mocked chunk object has the same attribute names as the internal section object of Construction
        # objects we can just directly compare them to see if it was properly added to the construction
        for original_section in _iter():
            section_coords = (
                original_section.sx,
                original_section.sy,
                original_section.sz,
            )
            self.assertEqual(
                original_section,
                construction_obj_1.sections[section_coords],
                f"Sections as {section_coords} are not equal",
            )

        save_start = time.time()
        construction_obj_1.save("test_construction_creation_2.construction")
        save_end = time.time()

        load_start = time.time()
        construction_obj_2 = Construction.load(
            "test_construction_creation_2.construction"
        )
        load_end = time.time()

        self.assertEqual(construction_obj_1, construction_obj_2)
        for original_section in _iter():
            section_coords = (
                original_section.sx,
                original_section.sy,
                original_section.sz,
            )
            self.assertEqual(
                original_section,
                construction_obj_2.sections[section_coords],
                f"Sections as {section_coords} are not equal",
            )

        print(f"Saving Took: {save_end - save_start:02.4f} seconds")
        print(f"Loading Took: {load_end - load_start:02.4f} seconds")


if __name__ == "__main__":
    unittest.main()
