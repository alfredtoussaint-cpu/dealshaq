"""
Basic smoke tests for DealShaq backend API.
These tests verify that the core modules can be imported and basic functions work.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpoints:
    """Test basic health and status endpoints"""
    
    def test_import_server(self):
        """Test that server module can be imported without errors"""
        with patch('motor.motor_asyncio.AsyncIOMotorClient'):
            with patch.dict('os.environ', {
                'MONGO_URL': 'mongodb://localhost:27017',
                'DB_NAME': 'test_db',
                'SECRET_KEY': 'test_secret_key'
            }):
                import server
                assert hasattr(server, 'app')

    def test_valid_categories_defined(self):
        """Test that VALID_CATEGORIES contains expected categories"""
        with patch('motor.motor_asyncio.AsyncIOMotorClient'):
            with patch.dict('os.environ', {
                'MONGO_URL': 'mongodb://localhost:27017',
                'DB_NAME': 'test_db',
                'SECRET_KEY': 'test_secret_key'
            }):
                import server
                assert len(server.VALID_CATEGORIES) == 20
                assert "Dairy & Eggs" in server.VALID_CATEGORIES
                assert "Fruits" in server.VALID_CATEGORIES
                assert "Vegetables" in server.VALID_CATEGORIES
                assert "Beverages" in server.VALID_CATEGORIES
                assert "Miscellaneous" in server.VALID_CATEGORIES


class TestCategorizationService:
    """Test the categorization service functionality"""
    
    def test_categorization_service_import(self):
        """Test that categorization_service can be imported"""
        import categorization_service
        assert hasattr(categorization_service, 'categorize_item')
        assert hasattr(categorization_service, 'CATEGORY_KEYWORDS')
    
    def test_category_keywords_coverage(self):
        """Test that category keywords cover all valid categories"""
        import categorization_service
        assert len(categorization_service.CATEGORY_KEYWORDS) >= 19
    
    def test_categorize_milk_by_keywords(self):
        """Test that milk items are categorized to Dairy & Eggs"""
        import categorization_service
        result = categorization_service.categorize_by_keywords("Organic 2% Milk")
        assert result == "Dairy & Eggs"
    
    def test_categorize_apple_by_keywords(self):
        """Test that apple items are categorized to Fruits"""
        import categorization_service
        result = categorization_service.categorize_by_keywords("Honeycrisp Apples")
        assert result == "Fruits"
    
    def test_organic_attribute_detection(self):
        """Test that organic items are correctly detected"""
        import categorization_service
        result = categorization_service.detect_attributes("Organic Greek Yogurt")
        assert result.get("is_organic", False) == True
    
    def test_brand_generic_parsing(self):
        """Test brand/generic name parsing"""
        import categorization_service
        result = categorization_service.parse_brand_and_generic("Quaker, Simply Granola")
        assert result.get("brand") == "Quaker"
        assert "Granola" in result.get("generic_name", "")
    
    def test_generic_item_parsing(self):
        """Test generic item (no brand) parsing"""
        import categorization_service
        result = categorization_service.parse_brand_and_generic("Granola")
        assert result.get("has_brand") == False


class TestBarcodeOCRService:
    """Test the barcode and OCR service"""
    
    def test_barcode_service_import(self):
        """Test that barcode_ocr_service can be imported"""
        import barcode_ocr_service
        assert hasattr(barcode_ocr_service, 'lookup_barcode')
        assert hasattr(barcode_ocr_service, 'map_to_dealshaq_category')
    
    def test_category_mapping_beverages(self):
        """Test that beverage category mapping works"""
        import barcode_ocr_service
        # Test common beverage keywords
        result = barcode_ocr_service.map_to_dealshaq_category("beverages,soft drinks,soda")
        assert result == "Beverages"
    
    def test_category_mapping_dairy(self):
        """Test that dairy category mapping works"""
        import barcode_ocr_service
        result = barcode_ocr_service.map_to_dealshaq_category("dairy,milk,cheese")
        assert result == "Dairy & Eggs"


class TestWebSocketService:
    """Test the WebSocket service"""
    
    def test_websocket_service_import(self):
        """Test that websocket_service can be imported"""
        import websocket_service
        assert hasattr(websocket_service, 'WebSocketManager')
    
    def test_websocket_manager_instantiation(self):
        """Test that WebSocketManager can be instantiated"""
        import websocket_service
        manager = websocket_service.WebSocketManager()
        assert hasattr(manager, 'active_connections')
        # Initial state should be empty
        assert len(manager.active_connections) == 0
