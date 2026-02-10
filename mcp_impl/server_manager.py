"""
MCP Server Manager

Handles starting and managing the HTTP MCP server lifecycle
"""

import threading
import time
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages the lifecycle of the HTTP MCP server"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.server = None
        self.thread = None
        self.is_running = False
    
    def start(self, host: str = "127.0.0.1", port: int = 8000, timeout: int = 10):
        """
        Start the HTTP MCP server in background thread
        
        Args:
            host: Server host
            port: Server port
            timeout: Seconds to wait for server startup
        
        Returns:
            bool: True if server started successfully
        """
        if self.is_running:
            logger.info("MCP server already running")
            return True
        
        logger.info(f"Starting HTTP MCP server on {host}:{port}...")
        
        try:
            # Import here to avoid circular imports
            from mcp_impl.server_http import app as mcp_app
            import uvicorn
            
            # Create Uvicorn config
            config = uvicorn.Config(
                app=mcp_app,
                host=host,
                port=port,
                log_level="info",
                access_log=False
            )
            self.server = uvicorn.Server(config)
            
            # Run in background thread
            self.thread = threading.Thread(
                target=lambda: asyncio.run(self.server.serve()),
                daemon=True
            )
            self.thread.start()
            
            # Wait for server to be ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    import httpx
                    response = httpx.get(f"http://{host}:{port}/health", timeout=1)
                    if response.status_code == 200:
                        self.is_running = True
                        logger.info(f"✓ MCP server ready on {host}:{port}")
                        return True
                except:
                    time.sleep(0.5)
            
            logger.error("MCP server failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    def stop(self):
        """Stop the MCP server"""
        if self.server and self.is_running:
            logger.info("Stopping MCP server...")
            try:
                self.server.should_exit = True
                if self.thread:
                    self.thread.join(timeout=5)
                self.is_running = False
                logger.info("✓ MCP server stopped")
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
