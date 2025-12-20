"""
Basic smoke tests for DealShaq backend API.
These tests verify that the core endpoints are accessible and return expected responses.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoints:
    """Test basic health and status endpoints"""
    
    def test_import_server(self):
        """Test that server module can be imported without errors"""
        # This test verifies that server.py can be imported
        # even without a database connection by mocking the motor client
        with patch('motor.motor_asyncio.AsyncIOMotorClient'):
            with patch.dict('os.environ', {
                'MONGO_URL': 'mongodb://localhost:27017',
                'DB_NAME': 'test_db',
                'SECRET_KEY': 'test_secret_key'
            }):
                # Import should not raise any errors
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
                # Should have 20 categories
                assert len(server.VALID_CATEGORIES) == 20
                # Key categories should exist
                assert "Dairy & Eggs" in server.VALID_CATEGORIES
                assert "Fruits" in server.VALID_CATEGORIES
                assert "Vegetables" in server.VALID_CATEGORIES
                assert "Beverages" in server.VALID_CATEGORIES
                assert "Miscellaneous" in server.VALID_CATEGORIES

    def test_user_roles_defined(self):
        """Test that user roles are properly defined"""
        with patch('motor.motor_asyncio.AsyncIOMotorClient'):
            with patch.dict('os.environ', {
                'MONGO_URL': 'mongodb://localhost:27017',
                'DB_NAME': 'test_db',
                'SECRET_KEY': 'test_secret_key'
            }):
                import server
                # DAC = Consumer, DRLP = Retailer
                assert hasattr(server, 'UserRole')


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
        # All 20 categories should have keywords
        assert len(categorization_service.CATEGORY_KEYWORDS) >= 19  # Miscellaneous is catch-all
    
    def test_categorize_milk_item(self):
        """Test that milk items are categorized to Dairy & Eggs"""
        import categorization_service
        result = categorization_service.categorize_item("Organic 2% Milk")
        assert result["category"] == "Dairy & Eggs"
    
    def test_categorize_apple_item(self):
        """Test that apple items are categorized to Fruits"""
        import categorization_service
        result = categorization_service.categorize_item("Honeycrisp Apples")
        assert result["category"] == "Fruits"
    
    def test_organic_attribute_detection(self):
        """Test that organic items are correctly detected"""
        import categorization_service
        result = categorization_service.categorize_item("Organic Greek Yogurt")
        assert result.get("is_organic", False) == True
    
    def test_brand_generic_parsing(self):
        """Test brand/generic name parsing"""
        import categorization_service
        result = categorization_service.categorize_item("Quaker, Simply Granola")
        assert result.get("brand") == "Quaker"
        assert "Granola" in result.get("generic_name", "")


class TestBarcodeOCRService:
    """Test the barcode and OCR service"""
    
    def test_barcode_service_import(self):
        """Test that barcode_ocr_service can be imported"""
        import barcode_ocr_service
        assert hasattr(barcode_ocr_service, 'lookup_barcode')
        assert hasattr(barcode_ocr_service, 'map_to_dealshaq_category')
    
    def test_category_mapping_function_exists(self):
        """Test that category mapping function is available"""
        import barcode_ocr_service
        # Should be able to map common categories
        result = barcode_ocr_service.map_to_dealshaq_category("dairy")
        assert result in ["Dairy & Eggs", "Miscellaneous"]


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
