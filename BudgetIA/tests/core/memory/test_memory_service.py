
import pytest
import os
import shutil
import json
from src.core.memory.memory_service import MemoryService

TEST_USER_DIR = "tests/data/temp_user"

@pytest.fixture
def memory_service():
    if os.path.exists(TEST_USER_DIR):
        shutil.rmtree(TEST_USER_DIR)
    os.makedirs(TEST_USER_DIR)
    
    service = MemoryService(user_data_dir=TEST_USER_DIR)
    yield service
    
    if os.path.exists(TEST_USER_DIR):
        shutil.rmtree(TEST_USER_DIR)

def test_add_fact(memory_service):
    result = memory_service.add_fact("preference", "I like simple spreadsheets")
    assert "Fact added" in result
    
    facts = memory_service.search_facts()
    assert len(facts) == 1
    assert facts[0]["content"] == "I like simple spreadsheets"

def test_no_duplicate_fact(memory_service):
    memory_service.add_fact("preference", "Same fact")
    result = memory_service.add_fact("preference", "Same fact")
    assert "Fact already known" in result
    assert len(memory_service.search_facts()) == 1

def test_update_fact(memory_service):
    memory_service.add_fact("transport", "I prefer Uber")
    
    # Update
    result = memory_service.update_fact("Uber", "I prefer Metro")
    assert "Fact updated" in result
    
    facts = memory_service.search_facts()
    assert len(facts) == 1
    assert facts[0]["content"] == "I prefer Metro"
    assert "updated_at" in facts[0]

def test_forget_fact(memory_service):
    memory_service.add_fact("diet", "I am vegan")
    
    result = memory_service.forget_fact("vegan")
    assert "Fact(s) forgotten" in result
    
    assert len(memory_service.search_facts()) == 0

def test_search_facts(memory_service):
    memory_service.add_fact("work", "I work at Google")
    memory_service.add_fact("hobby", "I play guitar")
    
    results = memory_service.search_facts("guitar")
    assert len(results) == 1
    assert results[0]["category"] == "hobby"

def test_context_string(memory_service):
    memory_service.add_fact("A", "Fact A")
    context = memory_service.get_context_string()
    assert "User Memories:" in context
    assert "[A] Fact A" in context
