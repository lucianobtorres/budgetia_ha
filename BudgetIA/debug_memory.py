
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

try:
    from src.core.memory.memory_service import MemoryService
    print("SUCCESS: Import worked.")
except Exception as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)

# Basic Test
import shutil
TEST_DIR = "debug_memory_data"
if os.path.exists(TEST_DIR):
    shutil.rmtree(TEST_DIR)
os.makedirs(TEST_DIR)

try:
    service = MemoryService(TEST_DIR)
    msg = service.add_fact("debug", "Is working")
    print(msg)
    facts = service.search_facts()
    print(f"Facts found: {len(facts)}")
    assert len(facts) == 1
    print("SUCCESS: Basic logic worked.")
finally:
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
