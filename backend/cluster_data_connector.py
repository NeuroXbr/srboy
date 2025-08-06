"""
Cluster Data Connector - SrBoy Enterprise Edition
Este módulo gerencia conexões com múltiplos clusters de dados para escalabilidade empresarial.

Clusters Suportados:
- Google Cloud Spanner (dados estruturados de catálogo)  
- Google BigTable (dados de comportamento e cookies)
- MongoDB (banco principal atual)

Estratégias de Roteamento:
- mongodb: Usar apenas MongoDB (atual)
- spanner: Redirecionar dados de catálogo para Spanner
- bigtable: Redirecionar dados de comportamento para BigTable  
- hybrid: Usar estratégia híbrida com balanceamento de carga
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from datetime import datetime
import json

# Setup logging
logger = logging.getLogger(__name__)

class ClusterDataConnector:
    """
    Conector central para gerenciar múltiplos clusters de dados.
    """
    
    def __init__(self):
        """Initialize cluster configurations"""
        self.cluster_strategy = os.environ.get('CLUSTER_DATA_STRATEGY', 'mongodb')
        self.routing_enabled = os.environ.get('CLUSTER_ROUTING_ENABLED', 'false').lower() == 'true'
        
        # MongoDB connection (primary)
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.mongo_client = None
        self.mongo_db = None
        
        # Google Cloud Spanner configuration
        self.spanner_enabled = os.environ.get('SPANNER_ENABLED', 'false').lower() == 'true'
        self.spanner_instance_id = os.environ.get('SPANNER_INSTANCE_ID', 'srboy-production')
        self.spanner_database_id = os.environ.get('SPANNER_DATABASE_ID', 'srboy-catalog')
        self.google_cloud_project = os.environ.get('GOOGLE_CLOUD_PROJECT', 'srboy-enterprise')
        self.spanner_client = None
        self.spanner_database = None
        
        # Google BigTable configuration
        self.bigtable_enabled = os.environ.get('BIGTABLE_ENABLED', 'false').lower() == 'true'
        self.bigtable_instance_id = os.environ.get('BIGTABLE_INSTANCE_ID', 'srboy-analytics')
        self.bigtable_table_prefix = os.environ.get('BIGTABLE_TABLE_PREFIX', 'srboy')
        self.bigtable_client = None
        self.bigtable_instance = None
        
        # Initialize connections
        self._initialize_connections()
        
        logger.info(f"Cluster Data Connector initialized with strategy: {self.cluster_strategy}")
    
    def _initialize_connections(self):
        """Initialize database connections based on configuration"""
        try:
            # Always initialize MongoDB (primary database)
            self._init_mongodb()
            
            # Initialize cloud databases if enabled
            if self.spanner_enabled and self.cluster_strategy in ['spanner', 'hybrid']:
                self._init_spanner()
            
            if self.bigtable_enabled and self.cluster_strategy in ['bigtable', 'hybrid']:
                self._init_bigtable()
                
        except Exception as e:
            logger.error(f"Error initializing cluster connections: {str(e)}")
            # Fallback to MongoDB only
            self.cluster_strategy = 'mongodb'
            self._init_mongodb()
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            self.mongo_client = MongoClient(self.mongo_url)
            self.mongo_db = self.mongo_client.srboy_db
            logger.info("MongoDB connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            raise
    
    def _init_spanner(self):
        """Initialize Google Cloud Spanner connection"""
        try:
            # Import Google Cloud Spanner (only if needed)
            from google.cloud import spanner
            
            # Initialize Spanner client
            self.spanner_client = spanner.Client(project=self.google_cloud_project)
            self.spanner_instance = self.spanner_client.instance(self.spanner_instance_id)
            self.spanner_database = self.spanner_instance.database(self.spanner_database_id)
            
            logger.info(f"Google Cloud Spanner connection initialized: {self.spanner_database_id}")
        except ImportError:
            logger.warning("Google Cloud Spanner client not installed. Install with: pip install google-cloud-spanner")
            self.spanner_enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Spanner: {str(e)}")
            self.spanner_enabled = False
    
    def _init_bigtable(self):
        """Initialize Google BigTable connection"""
        try:
            # Import Google Cloud BigTable (only if needed)
            from google.cloud import bigtable
            
            # Initialize BigTable client
            self.bigtable_client = bigtable.Client(project=self.google_cloud_project)
            self.bigtable_instance = self.bigtable_client.instance(self.bigtable_instance_id)
            
            logger.info(f"Google Cloud BigTable connection initialized: {self.bigtable_instance_id}")
        except ImportError:
            logger.warning("Google Cloud BigTable client not installed. Install with: pip install google-cloud-bigtable")
            self.bigtable_enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud BigTable: {str(e)}")
            self.bigtable_enabled = False
    
    def get_collection_connection(self, collection_name: str):
        """
        Get the appropriate database connection for a collection based on routing strategy.
        
        Args:
            collection_name: Nome da coleção (users, products, behavior_events, etc.)
        
        Returns:
            Tuple: (connection_type, connection_object)
        """
        # Define collection routing rules
        spanner_collections = [
            'products', 'product_categories', 'fastfood_menus', 'fastfood_items',
            'shopping_carts', 'cart_items', 'ecommerce_orders', 'inventory'
        ]
        
        bigtable_collections = [
            'user_behavior', 'page_views', 'click_events', 'user_sessions',
            'purchase_funnel', 'analytics_events'
        ]
        
        if self.cluster_strategy == 'spanner' and collection_name in spanner_collections and self.spanner_enabled:
            return ('spanner', self.spanner_database)
        
        elif self.cluster_strategy == 'bigtable' and collection_name in bigtable_collections and self.bigtable_enabled:
            return ('bigtable', self.bigtable_instance)
        
        elif self.cluster_strategy == 'hybrid':
            # Hybrid strategy: route to appropriate cluster
            if collection_name in spanner_collections and self.spanner_enabled:
                return ('spanner', self.spanner_database)
            elif collection_name in bigtable_collections and self.bigtable_enabled:
                return ('bigtable', self.bigtable_instance)
        
        # Default to MongoDB
        return ('mongodb', self.mongo_db[collection_name])
    
    def insert_document(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert document into appropriate cluster.
        
        Args:
            collection_name: Nome da coleção
            document: Documento a ser inserido
        
        Returns:
            Document ID or insertion result
        """
        connection_type, connection = self.get_collection_connection(collection_name)
        
        try:
            if connection_type == 'mongodb':
                result = connection.insert_one(document)
                return str(result.inserted_id)
            
            elif connection_type == 'spanner':
                return self._insert_spanner_document(collection_name, document)
            
            elif connection_type == 'bigtable':
                return self._insert_bigtable_document(collection_name, document)
                
        except Exception as e:
            logger.error(f"Error inserting document to {connection_type}: {str(e)}")
            # Fallback to MongoDB
            if connection_type != 'mongodb':
                mongo_collection = self.mongo_db[collection_name]
                result = mongo_collection.insert_one(document)
                return str(result.inserted_id)
            raise
    
    def find_documents(self, collection_name: str, query: Dict[str, Any] = None, limit: int = None) -> List[Dict]:
        """
        Find documents from appropriate cluster.
        
        Args:
            collection_name: Nome da coleção
            query: Query filter (MongoDB style)
            limit: Limit number of results
        
        Returns:
            List of documents
        """
        connection_type, connection = self.get_collection_connection(collection_name)
        
        try:
            if connection_type == 'mongodb':
                if query is None:
                    query = {}
                cursor = connection.find(query)
                if limit:
                    cursor = cursor.limit(limit)
                return list(cursor)
            
            elif connection_type == 'spanner':
                return self._find_spanner_documents(collection_name, query, limit)
            
            elif connection_type == 'bigtable':
                return self._find_bigtable_documents(collection_name, query, limit)
                
        except Exception as e:
            logger.error(f"Error finding documents from {connection_type}: {str(e)}")
            # Fallback to MongoDB
            if connection_type != 'mongodb':
                mongo_collection = self.mongo_db[collection_name]
                if query is None:
                    query = {}
                cursor = mongo_collection.find(query)
                if limit:
                    cursor = cursor.limit(limit)
                return list(cursor)
            raise
    
    def update_document(self, collection_name: str, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
        """
        Update document in appropriate cluster.
        
        Args:
            collection_name: Nome da coleção
            filter_query: Filter to find document
            update_data: Update operations
        
        Returns:
            Success status
        """
        connection_type, connection = self.get_collection_connection(collection_name)
        
        try:
            if connection_type == 'mongodb':
                result = connection.update_one(filter_query, update_data)
                return result.modified_count > 0
            
            elif connection_type == 'spanner':
                return self._update_spanner_document(collection_name, filter_query, update_data)
            
            elif connection_type == 'bigtable':
                return self._update_bigtable_document(collection_name, filter_query, update_data)
                
        except Exception as e:
            logger.error(f"Error updating document in {connection_type}: {str(e)}")
            # Fallback to MongoDB
            if connection_type != 'mongodb':
                mongo_collection = self.mongo_db[collection_name]
                result = mongo_collection.update_one(filter_query, update_data)
                return result.modified_count > 0
            raise
    
    def delete_document(self, collection_name: str, filter_query: Dict[str, Any]) -> bool:
        """
        Delete document from appropriate cluster.
        
        Args:
            collection_name: Nome da coleção
            filter_query: Filter to find document
        
        Returns:
            Success status
        """
        connection_type, connection = self.get_collection_connection(collection_name)
        
        try:
            if connection_type == 'mongodb':
                result = connection.delete_one(filter_query)
                return result.deleted_count > 0
            
            elif connection_type == 'spanner':
                return self._delete_spanner_document(collection_name, filter_query)
            
            elif connection_type == 'bigtable':
                return self._delete_bigtable_document(collection_name, filter_query)
                
        except Exception as e:
            logger.error(f"Error deleting document from {connection_type}: {str(e)}")
            # Fallback to MongoDB
            if connection_type != 'mongodb':
                mongo_collection = self.mongo_db[collection_name]
                result = mongo_collection.delete_one(filter_query)
                return result.deleted_count > 0
            raise
    
    # Spanner-specific methods (placeholders for future implementation)
    def _insert_spanner_document(self, table_name: str, document: Dict[str, Any]) -> str:
        """Insert document into Spanner (placeholder)"""
        # TODO: Implement Spanner insertion logic
        logger.info(f"Spanner insertion placeholder for table: {table_name}")
        
        # For now, create a mock transaction
        with self.spanner_database.snapshot() as snapshot:
            # This is a placeholder - real implementation would use mutations
            pass
        
        return f"spanner_{table_name}_{datetime.now().isoformat()}"
    
    def _find_spanner_documents(self, table_name: str, query: Dict[str, Any], limit: int) -> List[Dict]:
        """Find documents from Spanner (placeholder)"""
        # TODO: Implement Spanner query logic
        logger.info(f"Spanner query placeholder for table: {table_name}")
        return []
    
    def _update_spanner_document(self, table_name: str, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
        """Update document in Spanner (placeholder)"""
        # TODO: Implement Spanner update logic
        logger.info(f"Spanner update placeholder for table: {table_name}")
        return True
    
    def _delete_spanner_document(self, table_name: str, filter_query: Dict[str, Any]) -> bool:
        """Delete document from Spanner (placeholder)"""
        # TODO: Implement Spanner delete logic
        logger.info(f"Spanner delete placeholder for table: {table_name}")
        return True
    
    # BigTable-specific methods (placeholders for future implementation)
    def _insert_bigtable_document(self, table_name: str, document: Dict[str, Any]) -> str:
        """Insert document into BigTable (placeholder)"""
        # TODO: Implement BigTable insertion logic
        logger.info(f"BigTable insertion placeholder for table: {table_name}")
        
        # For now, get table reference
        table = self.bigtable_instance.table(f"{self.bigtable_table_prefix}_{table_name}")
        
        return f"bigtable_{table_name}_{datetime.now().isoformat()}"
    
    def _find_bigtable_documents(self, table_name: str, query: Dict[str, Any], limit: int) -> List[Dict]:
        """Find documents from BigTable (placeholder)"""
        # TODO: Implement BigTable query logic  
        logger.info(f"BigTable query placeholder for table: {table_name}")
        return []
    
    def _update_bigtable_document(self, table_name: str, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
        """Update document in BigTable (placeholder)"""
        # TODO: Implement BigTable update logic
        logger.info(f"BigTable update placeholder for table: {table_name}")
        return True
    
    def _delete_bigtable_document(self, table_name: str, filter_query: Dict[str, Any]) -> bool:
        """Delete document from BigTable (placeholder)"""
        # TODO: Implement BigTable delete logic
        logger.info(f"BigTable delete placeholder for table: {table_name}")
        return True
    
    def get_cluster_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all configured clusters.
        
        Returns:
            Health status of each cluster
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "cluster_strategy": self.cluster_strategy,
            "routing_enabled": self.routing_enabled,
            "clusters": {}
        }
        
        # MongoDB health check
        try:
            self.mongo_client.admin.command('ping')
            status["clusters"]["mongodb"] = {
                "status": "healthy",
                "url": self.mongo_url,
                "database": "srboy_db"
            }
        except Exception as e:
            status["clusters"]["mongodb"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # Spanner health check
        if self.spanner_enabled:
            try:
                # Simple health check for Spanner
                status["clusters"]["spanner"] = {
                    "status": "configured",
                    "instance_id": self.spanner_instance_id,
                    "database_id": self.spanner_database_id,
                    "project": self.google_cloud_project
                }
            except Exception as e:
                status["clusters"]["spanner"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # BigTable health check  
        if self.bigtable_enabled:
            try:
                status["clusters"]["bigtable"] = {
                    "status": "configured",
                    "instance_id": self.bigtable_instance_id,
                    "project": self.google_cloud_project
                }
            except Exception as e:
                status["clusters"]["bigtable"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status
    
    def close_connections(self):
        """Close all database connections"""
        try:
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
        
        # Spanner and BigTable clients don't need explicit closing


# Global cluster connector instance
cluster_connector = None

def get_cluster_connector() -> ClusterDataConnector:
    """
    Get or create global cluster connector instance.
    
    Returns:
        ClusterDataConnector instance
    """
    global cluster_connector
    
    if cluster_connector is None:
        cluster_connector = ClusterDataConnector()
    
    return cluster_connector


def get_collection(collection_name: str):
    """
    Get collection connection through cluster router.
    This function provides backward compatibility with existing code.
    
    Args:
        collection_name: Nome da coleção
    
    Returns:
        Collection connection (MongoDB, Spanner, or BigTable)
    """
    connector = get_cluster_connector()
    connection_type, connection = connector.get_collection_connection(collection_name)
    
    if connection_type == 'mongodb':
        return connection
    else:
        # For non-MongoDB connections, return a wrapper that maintains compatibility
        return ClusterCollectionWrapper(connector, collection_name, connection_type)


class ClusterCollectionWrapper:
    """
    Wrapper class to maintain MongoDB-like interface for other cluster types.
    This ensures existing code continues to work regardless of the underlying cluster.
    """
    
    def __init__(self, connector: ClusterDataConnector, collection_name: str, connection_type: str):
        self.connector = connector
        self.collection_name = collection_name
        self.connection_type = connection_type
    
    def insert_one(self, document: Dict[str, Any]):
        """MongoDB-compatible insert_one interface"""
        result_id = self.connector.insert_document(self.collection_name, document)
        
        # Create a result object that mimics PyMongo's InsertOneResult
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        
        return InsertResult(result_id)
    
    def find(self, query: Dict[str, Any] = None):
        """MongoDB-compatible find interface"""
        documents = self.connector.find_documents(self.collection_name, query)
        
        # Create a cursor-like object
        class CursorWrapper:
            def __init__(self, documents):
                self.documents = documents
                self._limit = None
                self._sort = None
            
            def limit(self, limit_value):
                self._limit = limit_value
                return self
            
            def sort(self, key, direction=1):
                self._sort = (key, direction)
                return self
            
            def __iter__(self):
                docs = self.documents
                if self._sort:
                    # Basic sorting implementation
                    key, direction = self._sort
                    docs = sorted(docs, key=lambda x: x.get(key, ''), reverse=(direction == -1))
                if self._limit:
                    docs = docs[:self._limit]
                return iter(docs)
            
            def __list__(self):
                return list(self.__iter__())
        
        return CursorWrapper(documents)
    
    def find_one(self, query: Dict[str, Any] = None):
        """MongoDB-compatible find_one interface"""
        documents = self.connector.find_documents(self.collection_name, query, limit=1)
        return documents[0] if documents else None
    
    def update_one(self, filter_query: Dict[str, Any], update_data: Dict[str, Any]):
        """MongoDB-compatible update_one interface"""
        success = self.connector.update_document(self.collection_name, filter_query, update_data)
        
        class UpdateResult:
            def __init__(self, modified_count):
                self.modified_count = modified_count
                
        return UpdateResult(1 if success else 0)
    
    def delete_one(self, filter_query: Dict[str, Any]):
        """MongoDB-compatible delete_one interface"""
        success = self.connector.delete_document(self.collection_name, filter_query)
        
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        
        return DeleteResult(1 if success else 0)
    
    def count_documents(self, query: Dict[str, Any] = None):
        """MongoDB-compatible count_documents interface"""
        documents = self.connector.find_documents(self.collection_name, query)
        return len(documents)


if __name__ == "__main__":
    # Test cluster connectivity
    connector = get_cluster_connector()
    health_status = connector.get_cluster_health_status()
    print(f"Cluster Health Status: {json.dumps(health_status, indent=2)}")