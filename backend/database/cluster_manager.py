"""
SrBoy Enterprise Database Cluster Manager
=========================================

Manages connections to multiple database clusters:
- Primary Cluster: Google Cloud Spanner (OLTP - Catalog, Orders, Users)
- Analytics Cluster: Google BigTable (OLAP - Behavior, Analytics, Logs)
- Fallback Cluster: MongoDB (Local development and backup)

READY FOR ENTERPRISE DEPLOYMENT
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import json
from contextlib import asynccontextmanager
from enum import Enum

# Google Cloud imports (installed when needed)
try:
    from google.cloud import spanner
    from google.cloud import bigtable
    from google.cloud.bigtable import column_family
    from google.cloud.bigtable import row_filters
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logging.warning("Google Cloud libraries not installed. Using fallback to MongoDB.")

# MongoDB fallback
import pymongo
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClusterType(Enum):
    PRIMARY = "primary"      # Spanner - OLTP
    ANALYTICS = "analytics"  # BigTable - OLAP  
    FALLBACK = "fallback"   # MongoDB - Local/Backup

class DataCategory(Enum):
    CATALOG = "catalog"           # Products, inventory, pricing
    USER_DATA = "user_data"       # User profiles, authentication
    TRANSACTIONAL = "transactional"  # Orders, payments, deliveries
    BEHAVIORAL = "behavioral"     # User behavior, analytics
    LOGGING = "logging"           # Application logs, events

class SrBoyClusterManager:
    """
    Enterprise Database Cluster Manager
    
    Routes data operations to appropriate clusters based on data type and performance requirements.
    Implements failover, load balancing, and health monitoring.
    """
    
    def __init__(self):
        self.clusters_enabled = os.environ.get('CLUSTER_ROUTING_ENABLED', 'false').lower() == 'true'
        self.spanner_enabled = os.environ.get('SPANNER_ENABLED', 'false').lower() == 'true'
        self.bigtable_enabled = os.environ.get('BIGTABLE_ENABLED', 'false').lower() == 'true'
        
        # Cluster connections
        self._spanner_client = None
        self._spanner_instance = None
        self._spanner_database = None
        self._bigtable_client = None
        self._bigtable_instance = None
        self._mongodb_client = None
        self._mongodb_db = None
        
        # Cluster health status
        self._cluster_health = {
            ClusterType.PRIMARY: True,
            ClusterType.ANALYTICS: True,
            ClusterType.FALLBACK: True
        }
        
        # Initialize connections
        asyncio.create_task(self._initialize_clusters())
    
    async def _initialize_clusters(self):
        """Initialize all database cluster connections"""
        try:
            # Initialize Spanner (Primary Cluster)
            if self.spanner_enabled and GOOGLE_CLOUD_AVAILABLE:
                await self._initialize_spanner()
            
            # Initialize BigTable (Analytics Cluster)
            if self.bigtable_enabled and GOOGLE_CLOUD_AVAILABLE:
                await self._initialize_bigtable()
            
            # Initialize MongoDB (Fallback Cluster)
            await self._initialize_mongodb()
            
            logger.info("✅ Database clusters initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing clusters: {str(e)}")
            # Fallback to MongoDB only
            await self._initialize_mongodb()
    
    async def _initialize_spanner(self):
        """Initialize Google Cloud Spanner connection"""
        try:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            instance_id = os.environ.get('SPANNER_INSTANCE_ID')
            database_id = os.environ.get('SPANNER_DATABASE_ID')
            
            if not all([project_id, instance_id, database_id]):
                raise ValueError("Spanner configuration incomplete")
            
            self._spanner_client = spanner.Client(project=project_id)
            self._spanner_instance = self._spanner_client.instance(instance_id)
            self._spanner_database = self._spanner_instance.database(database_id)
            
            # Test connection
            with self._spanner_database.snapshot() as snapshot:
                results = snapshot.execute_sql("SELECT 1")
                list(results)  # Consume results to test connection
            
            logger.info("✅ Spanner cluster connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Spanner connection failed: {str(e)}")
            self._cluster_health[ClusterType.PRIMARY] = False
            self.spanner_enabled = False
    
    async def _initialize_bigtable(self):
        """Initialize Google Cloud BigTable connection"""
        try:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            instance_id = os.environ.get('BIGTABLE_INSTANCE_ID')
            
            if not all([project_id, instance_id]):
                raise ValueError("BigTable configuration incomplete")
            
            self._bigtable_client = bigtable.Client(project=project_id, admin=True)
            self._bigtable_instance = self._bigtable_client.instance(instance_id)
            
            # Test connection
            if self._bigtable_instance.exists():
                logger.info("✅ BigTable cluster connected successfully")
            else:
                raise Exception("BigTable instance does not exist")
                
        except Exception as e:
            logger.error(f"❌ BigTable connection failed: {str(e)}")
            self._cluster_health[ClusterType.ANALYTICS] = False
            self.bigtable_enabled = False
    
    async def _initialize_mongodb(self):
        """Initialize MongoDB fallback connection"""
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/srboy_db')
            self._mongodb_client = MongoClient(mongo_url)
            self._mongodb_db = self._mongodb_client.get_default_database()
            
            # Test connection
            self._mongodb_client.admin.command('ismaster')
            
            logger.info("✅ MongoDB fallback connected successfully")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            self._cluster_health[ClusterType.FALLBACK] = False
    
    def get_cluster_for_operation(self, data_category: DataCategory, operation_type: str = "read") -> ClusterType:
        """
        Determine which cluster to use for a given operation
        
        Args:
            data_category: Type of data being accessed
            operation_type: "read", "write", "analytics"
            
        Returns:
            ClusterType to use for the operation
        """
        
        if not self.clusters_enabled:
            return ClusterType.FALLBACK
        
        # Route based on data category and operation type
        if data_category == DataCategory.BEHAVIORAL:
            if self.bigtable_enabled and self._cluster_health[ClusterType.ANALYTICS]:
                return ClusterType.ANALYTICS
            else:
                return ClusterType.FALLBACK
        
        elif data_category in [DataCategory.CATALOG, DataCategory.TRANSACTIONAL, DataCategory.USER_DATA]:
            if self.spanner_enabled and self._cluster_health[ClusterType.PRIMARY]:
                return ClusterType.PRIMARY
            else:
                return ClusterType.FALLBACK
        
        elif data_category == DataCategory.LOGGING:
            # Analytics cluster preferred for logs
            if self.bigtable_enabled and self._cluster_health[ClusterType.ANALYTICS]:
                return ClusterType.ANALYTICS
            else:
                return ClusterType.FALLBACK
        
        # Default to fallback
        return ClusterType.FALLBACK
    
    async def execute_spanner_query(self, query: str, params: dict = None) -> List[Dict]:
        """Execute query on Spanner cluster"""
        if not self.spanner_enabled or not self._spanner_database:
            raise Exception("Spanner cluster not available")
        
        try:
            with self._spanner_database.snapshot() as snapshot:
                if params:
                    results = snapshot.execute_sql(query, params)
                else:
                    results = snapshot.execute_sql(query)
                
                return [dict(zip([col.name for col in results._metadata], row)) for row in results]
                
        except Exception as e:
            logger.error(f"Spanner query error: {str(e)}")
            self._cluster_health[ClusterType.PRIMARY] = False
            raise
    
    async def execute_spanner_mutation(self, table: str, mutations: List[Dict]) -> bool:
        """Execute mutations on Spanner cluster"""
        if not self.spanner_enabled or not self._spanner_database:
            raise Exception("Spanner cluster not available")
        
        try:
            with self._spanner_database.batch() as batch:
                for mutation in mutations:
                    if mutation["operation"] == "insert":
                        batch.insert(
                            table=table,
                            columns=mutation["columns"],
                            values=mutation["values"]
                        )
                    elif mutation["operation"] == "update":
                        batch.update(
                            table=table,
                            columns=mutation["columns"], 
                            values=mutation["values"]
                        )
                    elif mutation["operation"] == "delete":
                        batch.delete(
                            table=table,
                            keyset=mutation["keyset"]
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"Spanner mutation error: {str(e)}")
            self._cluster_health[ClusterType.PRIMARY] = False
            raise
    
    async def write_bigtable_row(self, table_id: str, row_key: str, data: Dict[str, Any]) -> bool:
        """Write data to BigTable cluster"""
        if not self.bigtable_enabled or not self._bigtable_instance:
            raise Exception("BigTable cluster not available")
        
        try:
            table = self._bigtable_instance.table(table_id)
            row = table.direct_row(row_key)
            
            # Write data to column families
            timestamp = datetime.utcnow()
            
            for column_family_id, columns in data.items():
                for column_id, value in columns.items():
                    row.set_cell(
                        column_family_id=column_family_id,
                        column=column_id.encode('utf-8'),
                        value=str(value).encode('utf-8'),
                        timestamp=timestamp
                    )
            
            row.commit()
            return True
            
        except Exception as e:
            logger.error(f"BigTable write error: {str(e)}")
            self._cluster_health[ClusterType.ANALYTICS] = False
            raise
    
    async def read_bigtable_rows(self, table_id: str, row_keys: List[str] = None, filter_: Any = None) -> List[Dict]:
        """Read data from BigTable cluster"""
        if not self.bigtable_enabled or not self._bigtable_instance:
            raise Exception("BigTable cluster not available")
        
        try:
            table = self._bigtable_instance.table(table_id)
            
            if row_keys:
                rows = table.read_rows(row_keys=row_keys)
            else:
                rows = table.read_rows(filter_=filter_)
            
            result = []
            for row in rows:
                row_data = {"row_key": row.row_key.decode('utf-8'), "data": {}}
                
                for column_family_id, columns in row.cells.items():
                    row_data["data"][column_family_id] = {}
                    for column_id, cells in columns.items():
                        # Get latest value
                        latest_cell = cells[0]
                        row_data["data"][column_family_id][column_id.decode('utf-8')] = latest_cell.value.decode('utf-8')
                
                result.append(row_data)
            
            return result
            
        except Exception as e:
            logger.error(f"BigTable read error: {str(e)}")
            self._cluster_health[ClusterType.ANALYTICS] = False
            raise
    
    async def execute_mongodb_operation(self, collection: str, operation: str, query: dict = None, data: dict = None) -> Any:
        """Execute operation on MongoDB fallback cluster"""
        if not self._mongodb_db:
            raise Exception("MongoDB cluster not available")
        
        try:
            coll = self._mongodb_db[collection]
            
            if operation == "find":
                return list(coll.find(query or {}))
            elif operation == "find_one":
                return coll.find_one(query or {})
            elif operation == "insert_one":
                return coll.insert_one(data)
            elif operation == "insert_many":
                return coll.insert_many(data)
            elif operation == "update_one":
                return coll.update_one(query, {"$set": data})
            elif operation == "update_many":
                return coll.update_many(query, {"$set": data})
            elif operation == "delete_one":
                return coll.delete_one(query)
            elif operation == "delete_many":
                return coll.delete_many(query)
            elif operation == "count_documents":
                return coll.count_documents(query or {})
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"MongoDB operation error: {str(e)}")
            self._cluster_health[ClusterType.FALLBACK] = False
            raise
    
    async def health_check(self) -> Dict[ClusterType, bool]:
        """Check health of all clusters"""
        health_status = {}
        
        # Check Spanner
        if self.spanner_enabled and self._spanner_database:
            try:
                with self._spanner_database.snapshot() as snapshot:
                    results = snapshot.execute_sql("SELECT 1")
                    list(results)
                health_status[ClusterType.PRIMARY] = True
            except:
                health_status[ClusterType.PRIMARY] = False
                self._cluster_health[ClusterType.PRIMARY] = False
        else:
            health_status[ClusterType.PRIMARY] = False
        
        # Check BigTable
        if self.bigtable_enabled and self._bigtable_instance:
            try:
                health_status[ClusterType.ANALYTICS] = self._bigtable_instance.exists()
            except:
                health_status[ClusterType.ANALYTICS] = False
                self._cluster_health[ClusterType.ANALYTICS] = False
        else:
            health_status[ClusterType.ANALYTICS] = False
        
        # Check MongoDB
        if self._mongodb_client:
            try:
                self._mongodb_client.admin.command('ismaster')
                health_status[ClusterType.FALLBACK] = True
            except:
                health_status[ClusterType.FALLBACK] = False
                self._cluster_health[ClusterType.FALLBACK] = False
        else:
            health_status[ClusterType.FALLBACK] = False
        
        return health_status
    
    async def get_cluster_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all clusters"""
        return {
            "clusters_enabled": self.clusters_enabled,
            "spanner_enabled": self.spanner_enabled,
            "bigtable_enabled": self.bigtable_enabled,
            "cluster_health": dict(self._cluster_health),
            "routing_rules": {
                "catalog_data": "spanner" if self.spanner_enabled else "mongodb",
                "user_data": "spanner" if self.spanner_enabled else "mongodb", 
                "transactional_data": "spanner" if self.spanner_enabled else "mongodb",
                "behavioral_data": "bigtable" if self.bigtable_enabled else "mongodb",
                "logging_data": "bigtable" if self.bigtable_enabled else "mongodb"
            }
        }
    
    async def close_connections(self):
        """Close all cluster connections"""
        try:
            if self._spanner_client:
                self._spanner_client.close()
            
            if self._bigtable_client:
                self._bigtable_client.stop()
            
            if self._mongodb_client:
                self._mongodb_client.close()
                
            logger.info("✅ All cluster connections closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing connections: {str(e)}")

# Global cluster manager instance
cluster_manager = SrBoyClusterManager()

# Utility functions for easy access
async def get_cluster_for_data(data_category: DataCategory, operation_type: str = "read") -> ClusterType:
    """Get appropriate cluster for data operation"""
    return cluster_manager.get_cluster_for_operation(data_category, operation_type)

async def execute_cluster_operation(cluster_type: ClusterType, operation: str, **kwargs) -> Any:
    """Execute operation on specified cluster"""
    if cluster_type == ClusterType.PRIMARY:
        if operation == "query":
            return await cluster_manager.execute_spanner_query(kwargs["query"], kwargs.get("params"))
        elif operation == "mutation":
            return await cluster_manager.execute_spanner_mutation(kwargs["table"], kwargs["mutations"])
    
    elif cluster_type == ClusterType.ANALYTICS:
        if operation == "write":
            return await cluster_manager.write_bigtable_row(kwargs["table_id"], kwargs["row_key"], kwargs["data"])
        elif operation == "read":
            return await cluster_manager.read_bigtable_rows(kwargs["table_id"], kwargs.get("row_keys"), kwargs.get("filter_"))
    
    elif cluster_type == ClusterType.FALLBACK:
        return await cluster_manager.execute_mongodb_operation(
            kwargs["collection"], 
            kwargs["operation"], 
            kwargs.get("query"), 
            kwargs.get("data")
        )
    
    else:
        raise ValueError(f"Unsupported cluster type: {cluster_type}")

# Health monitoring
async def monitor_cluster_health():
    """Background task to monitor cluster health"""
    while True:
        try:
            await cluster_manager.health_check()
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Health monitoring error: {str(e)}")
            await asyncio.sleep(60)  # Wait longer on errors