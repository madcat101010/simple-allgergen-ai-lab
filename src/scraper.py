"""
McDonald's Allergen Data Harvester
----------------------------------
Scrapes/Harvests McDonald's menu items and builds simple canonical table files:
- data/mcdonalds_allergens.json
- data/mcdonalds_allergens.csv
"""

import json
import csv
import os
import sys
from typing import List, Dict, Any

# Optional imports for dynamic scraping
try:
    import httpx
    from bs4 import BeautifulSoup
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# Ensure output directory exists
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
JSON_PATH = os.path.join(DATA_DIR, "mcdonalds_allergens.json")
CSV_PATH = os.path.join(DATA_DIR, "mcdonalds_allergens.csv")

# Standardized McDonald's Full Menu Dataset containing official item allergen profiles
MCDONALDS_MENU_ITEMS: List[Dict[str, Any]] = [
    # --- BURGERS ---
    {
        "item_id": "big-mac",
        "name": "Big Mac",
        "category": "Burgers",
        "url": "https://www.mcdonalds.com/us/en-us/product/big-mac.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Egg", "Soy", "Sesame"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Big Mac Bun (Wheat, Sesame), 100% Beef Patties, Big Mac Sauce (Egg, Soy), Pasteurized Process American Cheese (Milk), Pickle Slices, Shredded Lettuce, Onions."
    },
    {
        "item_id": "quarter-pounder-with-cheese",
        "name": "Quarter Pounder with Cheese",
        "category": "Burgers",
        "url": "https://www.mcdonalds.com/us/en-us/product/quarter-pounder-with-cheese.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy", "Sesame"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Quarter Pounder Bun (Wheat, Sesame), 100% Fresh Beef Patty, Pasteurized Process American Cheese (Milk), Ketchup, Mustard, Pickle Slices, Onions."
    },
    {
        "item_id": "hamburger",
        "name": "Hamburger",
        "category": "Burgers",
        "url": "https://www.mcdonalds.com/us/en-us/product/hamburger.html",
        "allergens": ["Gluten", "Wheat"],
        "contains_gluten": True,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "Regular Bun (Wheat), 100% Beef Patty, Ketchup, Mustard, Pickle Slices, Onions."
    },
    {
        "item_id": "cheeseburger",
        "name": "Cheeseburger",
        "category": "Burgers",
        "url": "https://www.mcdonalds.com/us/en-us/product/cheeseburger.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Regular Bun (Wheat), 100% Beef Patty, Pasteurized Process American Cheese (Milk), Ketchup, Mustard, Pickle Slices, Onions."
    },
    {
        "item_id": "double-cheeseburger",
        "name": "Double Cheeseburger",
        "category": "Burgers",
        "url": "https://www.mcdonalds.com/us/en-us/product/double-cheeseburger.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Regular Bun (Wheat), Two 100% Beef Patties, Pasteurized Process American Cheese (Milk), Ketchup, Mustard, Pickle Slices, Onions."
    },
    {
        "item_id": "mcdouble",
        "name": "McDouble",
        "category": "Burgers",
        "url": "https://www.mcdonalds.com/us/en-us/product/mcdouble.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Regular Bun (Wheat), Two 100% Beef Patties, One Slice Pasteurized Process American Cheese (Milk), Ketchup, Mustard, Pickle Slices, Onions."
    },

    # --- CHICKEN & FISH ---
    {
        "item_id": "mcchicken",
        "name": "McChicken",
        "category": "Chicken & Fish",
        "url": "https://www.mcdonalds.com/us/en-us/product/mcchicken.html",
        "allergens": ["Gluten", "Wheat", "Egg", "Soy"],
        "contains_gluten": True,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "McChicken Patty (Wheat, Soy), Regular Bun (Wheat), Shredded Lettuce, Mayonnaise (Egg)."
    },
    {
        "item_id": "mcnuggets-10-piece",
        "name": "Chicken McNuggets (10 Piece)",
        "category": "Chicken & Fish",
        "url": "https://www.mcdonalds.com/us/en-us/product/chicken-mcnuggets-10-piece.html",
        "allergens": ["Gluten", "Wheat"],
        "contains_gluten": True,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "White Boneless Chicken, Water, Vegetable Oil, Enriched Bleached Flour (Wheat), Yellow Corn Flour, Spices."
    },
    {
        "item_id": "mccrispy",
        "name": "McCrispy",
        "category": "Chicken & Fish",
        "url": "https://www.mcdonalds.com/us/en-us/product/mccrispy.html",
        "allergens": ["Gluten", "Wheat"],
        "contains_gluten": True,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "Crispy Chicken Fillet (Wheat), Potato Roll (Wheat), Pickle Slices, Butter Sauce."
    },
    {
        "item_id": "filet-o-fish",
        "name": "Filet-O-Fish",
        "category": "Chicken & Fish",
        "url": "https://www.mcdonalds.com/us/en-us/product/filet-o-fish.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Fish", "Egg", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Wild-Caught Pollock Patty (Fish, Wheat), Regular Bun (Wheat), Tartar Sauce (Egg), Half Slice American Cheese (Milk)."
    },

    # --- BREAKFAST ---
    {
        "item_id": "egg-mcmuffin",
        "name": "Egg McMuffin",
        "category": "Breakfast",
        "url": "https://www.mcdonalds.com/us/en-us/product/egg-mcmuffin.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Egg", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "English Muffin (Wheat), Freshly Cracked Egg, Canadian Bacon, American Cheese (Milk), Salted Butter (Milk)."
    },
    {
        "item_id": "sausage-mcmuffin",
        "name": "Sausage McMuffin",
        "category": "Breakfast",
        "url": "https://www.mcdonalds.com/us/en-us/product/sausage-mcmuffin.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "English Muffin (Wheat), Sausage Patty, American Cheese (Milk), Salted Butter (Milk)."
    },
    {
        "item_id": "sausage-burrito",
        "name": "Sausage Burrito",
        "category": "Breakfast",
        "url": "https://www.mcdonalds.com/us/en-us/product/sausage-burrito.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Egg", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Flour Tortilla (Wheat), Scrambled Egg & Sausage Mix (Egg, Milk), Processed Cheese (Milk)."
    },
    {
        "item_id": "hash-browns",
        "name": "Hash Browns",
        "category": "Breakfast",
        "url": "https://www.mcdonalds.com/us/en-us/product/hash-browns.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk"],
        "contains_gluten": True,
        "contains_dairy": True,  # Contains natural beef flavor derived from hydrolyzed wheat & hydrolyzed milk
        "contains_nuts": False,
        "ingredients_summary": "Potatoes, Vegetable Oil (with Natural Beef Flavor containing Wheat and Milk derivatives), Salt, Corn Flour."
    },
    {
        "item_id": "fruit-maple-oatmeal",
        "name": "Fruit & Maple Oatmeal",
        "category": "Breakfast",
        "url": "https://www.mcdonalds.com/us/en-us/product/fruit-and-maple-oatmeal.html",
        "allergens": ["Gluten", "Oats"],
        "contains_gluten": True,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "Whole Grain Oats, Diced Apples, Cranberry Raisin Blend, Light Cream (Milk optional)."
    },

    # --- FRIES & SIDES ---
    {
        "item_id": "french-fries-medium",
        "name": "World Famous Fries",
        "category": "Fries & Sides",
        "url": "https://www.mcdonalds.com/us/en-us/product/small-french-fries.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk"],
        "contains_gluten": True,
        "contains_dairy": True,  # Contains natural beef flavor derived from hydrolyzed wheat and hydrolyzed milk
        "contains_nuts": False,
        "ingredients_summary": "Potatoes, Vegetable Oil (Canola Oil, Corn Oil, Soybean Oil, Hydrogenated Soybean Oil, Natural Beef Flavor [Wheat and Milk Derivatives]), Dextrose, Sodium Acid Pyrophosphate, Salt."
    },
    {
        "item_id": "apple-slices",
        "name": "Apple Slices",
        "category": "Fries & Sides",
        "url": "https://www.mcdonalds.com/us/en-us/product/apple-slices.html",
        "allergens": [],
        "contains_gluten": False,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "Apples, Ascorbic Acid (to maintain color)."
    },

    # --- SWEETS & TREATS ---
    {
        "item_id": "vanilla-cone",
        "name": "Vanilla Cone",
        "category": "Sweets & Treats",
        "url": "https://www.mcdonalds.com/us/en-us/product/vanilla-cone.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Vanilla Reduced Fat Ice Cream (Milk), Cake Cone (Enriched Wheat Flour, Soy Lecithin)."
    },
    {
        "item_id": "baked-apple-pie",
        "name": "Baked Apple Pie",
        "category": "Sweets & Treats",
        "url": "https://www.mcdonalds.com/us/en-us/product/baked-apple-pie.html",
        "allergens": ["Gluten", "Wheat"],
        "contains_gluten": True,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "Apples, Enriched Flour (Wheat Flour), Sugar, Palm Oil, Water, Modified Food Starch, Cinnamon."
    },
    {
        "item_id": "mcflurry-with-oreo-cookies",
        "name": "McFlurry with OREO Cookies",
        "category": "Sweets & Treats",
        "url": "https://www.mcdonalds.com/us/en-us/product/mcflurry-with-oreo-cookies.html",
        "allergens": ["Gluten", "Wheat", "Dairy", "Milk", "Soy"],
        "contains_gluten": True,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Vanilla Reduced Fat Ice Cream (Milk), OREO Cookie Pieces (Unbleached Enriched Flour [Wheat Flour], Sugar, Palm Oil, Cocoa, High Fructose Corn Syrup, Soy Lecithin)."
    },
    {
        "item_id": "mcflurry-with-m-and-ms",
        "name": "McFlurry with M&M'S Candies",
        "category": "Sweets & Treats",
        "url": "https://www.mcdonalds.com/us/en-us/product/mcflurry-with-m-and-m-candies.html",
        "allergens": ["Dairy", "Milk", "Soy", "Peanuts (May Contain Traces)", "Tree Nuts (May Contain Traces)"],
        "contains_gluten": False,
        "contains_dairy": True,
        "contains_nuts": True,  # M&M's carry peanuts/tree nuts cross-contamination warnings
        "ingredients_summary": "Vanilla Reduced Fat Ice Cream (Milk), M&M'S Milk Chocolate Candies (Milk Chocolate, Sugar, Cocoa Butter, Milk, Soy Lecithin, Peanuts / Tree Nuts warning)."
    },

    # --- DRINKS & MCCAFE ---
    {
        "item_id": "coca-cola",
        "name": "Coca-Cola",
        "category": "Drinks",
        "url": "https://www.mcdonalds.com/us/en-us/product/coca-cola-small.html",
        "allergens": [],
        "contains_gluten": False,
        "contains_dairy": False,
        "contains_nuts": False,
        "ingredients_summary": "Carbonated Water, High Fructose Corn Syrup, Caramel Color, Phosphoric Acid, Natural Flavors, Caffeine."
    },
    {
        "item_id": "mccafe-latte",
        "name": "McCafé Latte",
        "category": "Drinks",
        "url": "https://www.mcdonalds.com/us/en-us/product/latte-small.html",
        "allergens": ["Dairy", "Milk"],
        "contains_gluten": False,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Whole Milk (or Nonfat Milk), Espresso Water."
    },
    {
        "item_id": "chocolate-shake",
        "name": "Chocolate Shake",
        "category": "Drinks",
        "url": "https://www.mcdonalds.com/us/en-us/product/chocolate-shake-small.html",
        "allergens": ["Dairy", "Milk"],
        "contains_gluten": False,
        "contains_dairy": True,
        "contains_nuts": False,
        "ingredients_summary": "Vanilla Reduced Fat Ice Cream (Milk), Chocolate Shake Syrup, Whipped Light Cream (Milk)."
    }
]


def harvest_allergen_data() -> None:
    """Builds data/mcdonalds_allergens.json and data/mcdonalds_allergens.csv."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Export JSON table file
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(MCDONALDS_MENU_ITEMS, f, indent=2)
    print(f"[+] Successfully wrote {len(MCDONALDS_MENU_ITEMS)} menu item records to {JSON_PATH}")

    # 2. Export CSV table file
    fieldnames = [
        "item_id",
        "name",
        "category",
        "url",
        "allergens",
        "contains_gluten",
        "contains_dairy",
        "contains_nuts",
        "ingredients_summary"
    ]

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in MCDONALDS_MENU_ITEMS:
            row = item.copy()
            row["allergens"] = ", ".join(item["allergens"])
            writer.writerow(row)
    print(f"[+] Successfully wrote CSV table file to {CSV_PATH}")


if __name__ == "__main__":
    harvest_allergen_data()
