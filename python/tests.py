from __future__ import annotations

import time
import unittest
import glob
import os
from itertools import product
from typing import Tuple

import numpy as np

from amulet.api import blockstate_to_block

from python.construction import ConstructionReader, ConstructionWriter, ConstructionSection

REMOVE_TEST_GENERATED_FILES = True
RUN_STRESS_TEST = False

TEST_EDITION = "java"
TEST_VERSION = (1, 13, 2)


class ConstructionTestCase(unittest.TestCase):
    small_block_palette = [
        blockstate_to_block("minecraft:air"),
        blockstate_to_block("minecraft:stone"),
        blockstate_to_block("minecraft:oak_planks"),
        blockstate_to_block("minecraft:diamond_block"),
        blockstate_to_block("minecraft:dirt"),
        blockstate_to_block("minecraft:lime_concrete"),
        blockstate_to_block("minecraft:orange_concrete"),
        blockstate_to_block("minecraft:quartz_block"),
        blockstate_to_block("minecraft:stone")
        + blockstate_to_block("minecraft:damaged_anvil[facing=south]"),
    ]

    def tearDown(self) -> None:
        if not REMOVE_TEST_GENERATED_FILES:
            return
        files_to_remove = glob.iglob("*.construction")
        for f in files_to_remove:
            os.remove(f)

    def test_non_cube_sections(self):
        min_pos = (0, 0, 0)
        shape = (8, 16, 8)
        blocks = np.zeros(shape, dtype=int)
        blocks[0:8, 0:8, 0:8] = 1
        blocks[8:16, 8:16, 8:16] = 8
        entities = []
        block_entities = []

        with ConstructionWriter("test_non_cube_sections.construction", TEST_EDITION, TEST_VERSION) as construction:
            construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)

        with ConstructionReader("test_non_cube_sections.construction") as construction:
            section = construction.read(0)

        self.assertEqual(section, ConstructionSection(min_pos, shape, blocks, entities, block_entities))

    @staticmethod
    def _blocks_1() -> Tuple[np.ndarray, Tuple[int, int, int]]:
        shape = (16, 16, 16)
        blocks = np.zeros(shape, dtype=int)
        blocks[0:8, 0:8, 0:8] = 1
        blocks[0:8, 0:8, 8:16] = 2
        blocks[0:8, 8:16, 0:8] = 3
        blocks[0:8, 8:16, 8:16] = 4
        blocks[8:16, 0:8, 0:8] = 5
        blocks[8:16, 0:8, 8:16] = 6
        blocks[8:16, 8:16, 0:8] = 7
        blocks[8:16, 8:16, 8:16] = 8
        return blocks, shape

    def test_construction_creation_1(self):
        min_pos = (0, 0, 0)
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        with ConstructionWriter("test_construction_creation_1.construction", TEST_EDITION, TEST_VERSION) as construction:
            construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)

        with ConstructionReader("test_construction_creation_1.construction") as construction:
            section = construction.read(0)

        self.assertEqual(section, ConstructionSection(min_pos, shape, blocks, entities, block_entities))

    def test_construction_non_contiguous_1(self):
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        sections = []

        with ConstructionWriter("test_construction_non_contiguous_1.construction", TEST_EDITION, TEST_VERSION) as construction:
            for min_pos in product(range(0, 48, 16), range(0, 48, 16), range(0, 48, 16)):
                if min_pos != (1, 1, 1):
                    construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)
                    sections.append(ConstructionSection(min_pos, shape, blocks, entities, block_entities))

        with ConstructionReader("test_construction_non_contiguous_1.construction") as construction:
            sections2 = [construction.read(i) for i in range(len(construction.sections))]

        self.assertEqual(sections, sections2)

    def test_construction_non_contiguous_2(self):
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        sections = []

        with ConstructionWriter("test_construction_non_contiguous_2.construction", TEST_EDITION, TEST_VERSION) as construction:
            for min_pos in product(range(0, 48, 16), range(0, 48, 16), range(0, 48, 16)):
                if 1 not in min_pos:
                    construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)
                    sections.append(ConstructionSection(min_pos, shape, blocks, entities, block_entities))

        with ConstructionReader("test_construction_non_contiguous_2.construction") as construction:
            sections2 = [construction.read(i) for i in range(len(construction.sections))]

        self.assertEqual(sections, sections2)

    def test_construction_boundary_1(self):
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        block_layout_2 = np.zeros((16, 16, 16), dtype=int)
        block_layout_2[0:8, 0:8, 0:8] = 1
        block_layout_2[0:8, 0:8, 8:16] = 2
        block_layout_2[0:8, 8:16, 0:8] = 3
        block_layout_2[0:8, 8:16, 8:15] = 4
        block_layout_2[8:16, 0:8, 0:8] = 5
        block_layout_2[8:16, 0:8, 8:15] = 6
        block_layout_2[8:16, 8:16, 0:8] = 7
        block_layout_2[8:16, 8:16, 8:15] = 8

        block_layout_3 = np.zeros((16, 16, 16), dtype=int)
        block_layout_3[0:8, 0:8, 0:8] = 1
        block_layout_3[0:8, 0:8, 8:16] = 2
        block_layout_3[0:8, 8:16, 0:8] = 3
        block_layout_3[0:8, 8:16, 8:16] = 4
        block_layout_3[8:15, 0:8, 0:8] = 5
        block_layout_3[8:15, 0:8, 8:16] = 6
        block_layout_3[8:15, 8:16, 0:8] = 7
        block_layout_3[8:15, 8:16, 8:16] = 8

        block_layout_4 = np.zeros((16, 16, 16), dtype=int)
        block_layout_4[0:8, 0:8, 0:8] = 1
        block_layout_4[0:8, 0:8, 8:15] = 2
        block_layout_4[0:8, 8:16, 0:8] = 3
        block_layout_4[0:8, 8:16, 8:15] = 4
        block_layout_4[8:15, 0:8, 0:8] = 5
        block_layout_4[8:15, 0:8, 8:15] = 6
        block_layout_4[8:15, 8:16, 0:8] = 7
        block_layout_4[8:15, 8:16, 8:15] = 8

        sections = []

        with ConstructionWriter("test_construction_boundary_1.construction", TEST_EDITION, TEST_VERSION) as construction:
            for min_pos in product(range(0, 48, 16), range(0, 16, 16), range(0, 48, 16)):
                if min_pos[0] == 32 and min_pos[2] == 32:
                    construction.write(min_pos, shape, block_layout_4, self.small_block_palette, entities, block_entities)
                    sections.append(ConstructionSection(min_pos, shape, block_layout_4, entities, block_entities))
                elif min_pos[0] == 32:
                    construction.write(min_pos, shape, block_layout_3, self.small_block_palette, entities, block_entities)
                    sections.append(ConstructionSection(min_pos, shape, block_layout_3, entities, block_entities))
                elif min_pos[2] == 32:
                    construction.write(min_pos, shape, block_layout_2, self.small_block_palette, entities, block_entities)
                    sections.append(ConstructionSection(min_pos, shape, block_layout_2, entities, block_entities))
                else:
                    construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)
                    sections.append(ConstructionSection(min_pos, shape, blocks, entities, block_entities))

        with ConstructionReader("test_construction_boundary_1.construction") as construction:
            sections2 = [construction.read(i) for i in range(len(construction.sections))]

        self.assertEqual(sections, sections2)

    @unittest.skipUnless(RUN_STRESS_TEST, "Stress tests not enabled")
    def test_construction_creation_2(self):
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        sections = []

        save_start = time.time()
        with ConstructionWriter("test_construction_creation_2.construction", TEST_EDITION, TEST_VERSION) as construction:
            for min_pos in product(range(0, 16 * 50, 16), range(0, 16 * 50, 16), range(0, 16 * 50, 16)):
                construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)
                sections.append(ConstructionSection(min_pos, shape, blocks, entities, block_entities))
        save_end = time.time()

        load_start = time.time()
        with ConstructionReader("test_construction_creation_2.construction") as construction:
            sections2 = [construction.read(i) for i in range(len(construction.sections))]
        load_end = time.time()

        self.assertEqual(sections, sections2)

        print(f"Saving Took: {save_end - save_start:02.4f} seconds")
        print(f"Loading Took: {load_end - load_start:02.4f} seconds")

    def test_construction_creation_3(self):
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        with ConstructionWriter("test_construction_creation_3.construction", TEST_EDITION, TEST_VERSION) as construction:
            construction.write((2, 2, 2), shape, blocks, self.small_block_palette, entities, block_entities)
            section = ConstructionSection((2, 2, 2), shape, blocks, entities, block_entities)

        with ConstructionReader("test_construction_creation_3.construction") as construction:
            self.assertEqual(1, len(construction.sections))
            self.assertEqual(section, construction.read(0))

    def test_stacking(self):
        blocks, shape = self._blocks_1()
        entities = []
        block_entities = []

        sections = []

        with ConstructionWriter("test_stacking.construction", TEST_EDITION, TEST_VERSION) as construction:
            for min_pos in product(range(0, 16, 16), range(0, 48, 16), range(0, 16, 16)):
                construction.write(min_pos, shape, blocks, self.small_block_palette, entities, block_entities)
                sections.append(ConstructionSection(min_pos, shape, blocks, entities, block_entities))

        with ConstructionReader("test_stacking.construction") as construction:
            sections2 = [construction.read(i) for i in range(len(construction.sections))]

        self.assertEqual(sections, sections2)


if __name__ == "__main__":
    unittest.main()
