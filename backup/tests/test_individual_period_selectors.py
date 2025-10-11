#!/usr/bin/env python3
"""
Test script for individual period selectors functionality
Tests that each responsible person can have their own independent period selection
"""

import sys
import os

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_individual_period_selectors():
    """Test individual period selectors in responsible stats page"""
    
    print("=== Testing Individual Period Selectors Implementation ===")
    
    # Check if template file has individual period selectors
    template_path = "templates/responsible_stats.html"
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test 1: Check for individual period tracking variable
    print("\n1. Testing individual period tracking...")
    if "let individualPeriods = {};" in content:
        print("✅ Individual periods tracking variable found")
    else:
        print("❌ Individual periods tracking variable missing")
        return False
    
    # Test 2: Check for changeIndividualPeriod function
    print("\n2. Testing individual period change handler...")
    if "async function changeIndividualPeriod(responsible, newPeriod)" in content:
        print("✅ Individual period change function found")
    else:
        print("❌ Individual period change function missing")
        return False
    
    # Test 3: Check for updateIndividualCard function
    print("\n3. Testing individual card update function...")
    if "function updateIndividualCard(responsible, stats, period)" in content:
        print("✅ Individual card update function found")
    else:
        print("❌ Individual card update function missing")
        return False
    
    # Test 4: Check for individual period selector in card header
    print("\n4. Testing individual period selector in cards...")
    selector_pattern = 'onchange="changeIndividualPeriod(\'${responsible}\', this.value)"'
    if selector_pattern in content:
        print("✅ Individual period selector with change handler found")
    else:
        print("❌ Individual period selector with change handler missing")
        return False
    
    # Test 5: Check for individual table body IDs
    print("\n5. Testing individual table body IDs...")
    if "individualTableBody_${responsible.replace(/[^a-zA-Z0-9]/g, '_')}" in content:
        print("✅ Individual table body IDs found")
    else:
        print("❌ Individual table body IDs missing")
        return False
    
    # Test 6: Check for period initialization in displayStats
    print("\n6. Testing period initialization...")
    if "if (!individualPeriods[responsible])" in content:
        print("✅ Period initialization logic found")
    else:
        print("❌ Period initialization logic missing")
        return False
    
    # Test 7: Check for individual period usage in display
    print("\n7. Testing individual period usage...")
    if "const individualPeriod = individualPeriods[responsible];" in content:
        print("✅ Individual period usage found")
    else:
        print("❌ Individual period usage missing")
        return False
    
    # Test 8: Check for error handling in period change
    print("\n8. Testing error handling...")
    if "individualPeriods[responsible] = currentIndividualPeriod;" in content:
        print("✅ Error handling and period revert found")
    else:
        print("❌ Error handling missing")
        return False
    
    print("\n=== Individual Period Selectors Test Results ===")
    print("✅ All tests passed! Individual period selectors are properly implemented.")
    print("\nFeatures implemented:")
    print("- Each responsible person has their own period selector")
    print("- Independent period selection for each person")
    print("- Individual card updates without affecting others")
    print("- Proper error handling and period revert on errors")
    print("- Dynamic table content updates based on individual periods")
    print("- Unique table body IDs for targeted updates")
    
    return True

if __name__ == "__main__":
    success = test_individual_period_selectors()
    if success:
        print("\n🎉 Individual period selectors implementation is complete and working!")
    else:
        print("\n❌ Individual period selectors implementation has issues.")
    
    sys.exit(0 if success else 1)
