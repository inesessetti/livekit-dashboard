"""Multi-server configuration management"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Configuration for a single LiveKit server"""
    id: str
    name: str
    url: str
    api_key: str
    api_secret: str
    sip_enabled: bool = False
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.id:
            raise ValueError("Server ID is required")
        if not self.name:
            raise ValueError("Server name is required")
        if not self.url:
            raise ValueError("Server URL is required")
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.api_secret:
            raise ValueError("API secret is required")


class ServerConfigManager:
    """Manages multiple LiveKit server configurations"""
    
    def __init__(self):
        self._servers: Dict[str, ServerConfig] = {}
        self._default_server_id: Optional[str] = None
        self._load_configurations()
    
    def _load_configurations(self):
        """Load server configurations from environment variables"""
        # Method 1: Load from LIVEKIT_SERVERS JSON environment variable
        servers_json = os.environ.get("LIVEKIT_SERVERS")
        if servers_json:
            try:
                servers_data = json.loads(servers_json)
                for server_data in servers_data:
                    server = ServerConfig(**server_data)
                    self._servers[server.id] = server
                    if not self._default_server_id:
                        self._default_server_id = server.id
                return
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Warning: Failed to parse LIVEKIT_SERVERS JSON: {e}")
        
        # Method 2: Load from individual environment variables (backward compatibility)
        primary_url = os.environ.get("LIVEKIT_URL")
        primary_key = os.environ.get("LIVEKIT_API_KEY")
        primary_secret = os.environ.get("LIVEKIT_API_SECRET")
        primary_sip = os.environ.get("ENABLE_SIP", "false").lower() == "true"
        
        if primary_url and primary_key and primary_secret:
            primary_server = ServerConfig(
                id="primary",
                name="Primary Server",
                url=primary_url,
                api_key=primary_key,
                api_secret=primary_secret,
                sip_enabled=primary_sip,
                description="Primary LiveKit server"
            )
            self._servers["primary"] = primary_server
            self._default_server_id = "primary"
        
        # Method 3: Load additional servers from numbered environment variables
        server_index = 1
        while True:
            server_url = os.environ.get(f"LIVEKIT_URL_{server_index}")
            server_key = os.environ.get(f"LIVEKIT_API_KEY_{server_index}")
            server_secret = os.environ.get(f"LIVEKIT_API_SECRET_{server_index}")
            server_name = os.environ.get(f"LIVEKIT_NAME_{server_index}", f"Server {server_index}")
            server_sip = os.environ.get(f"ENABLE_SIP_{server_index}", "false").lower() == "true"
            
            if not (server_url and server_key and server_secret):
                break
            
            server_id = f"server_{server_index}"
            server = ServerConfig(
                id=server_id,
                name=server_name,
                url=server_url,
                api_key=server_key,
                api_secret=server_secret,
                sip_enabled=server_sip,
                description=f"LiveKit server {server_index}"
            )
            self._servers[server_id] = server
            
            # Set as default if it's the first one and no primary exists
            if not self._default_server_id:
                self._default_server_id = server_id
            
            server_index += 1
        
        if not self._servers:
            raise ValueError(
                "No LiveKit server configurations found. Please set LIVEKIT_URL, "
                "LIVEKIT_API_KEY, and LIVEKIT_API_SECRET environment variables, "
                "or provide LIVEKIT_SERVERS JSON configuration."
            )
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get server configuration by ID"""
        return self._servers.get(server_id)
    
    def get_default_server(self) -> Optional[ServerConfig]:
        """Get the default server configuration"""
        if self._default_server_id:
            return self._servers.get(self._default_server_id)
        return None
    
    def list_servers(self) -> List[ServerConfig]:
        """Get all server configurations"""
        return list(self._servers.values())
    
    def get_server_ids(self) -> List[str]:
        """Get all server IDs"""
        return list(self._servers.keys())
    
    def has_multiple_servers(self) -> bool:
        """Check if multiple servers are configured"""
        return len(self._servers) > 1
    
    def set_default_server(self, server_id: str) -> bool:
        """Set the default server"""
        if server_id in self._servers:
            self._default_server_id = server_id
            return True
        return False


# Global instance
_server_config_manager = None


def get_server_config_manager() -> ServerConfigManager:
    """Get the global server configuration manager"""
    global _server_config_manager
    if _server_config_manager is None:
        _server_config_manager = ServerConfigManager()
    return _server_config_manager


def get_server_config(server_id: Optional[str] = None) -> ServerConfig:
    """Get server configuration by ID or default"""
    manager = get_server_config_manager()
    
    if server_id:
        config = manager.get_server(server_id)
        if config:
            return config
        raise ValueError(f"Server configuration not found: {server_id}")
    
    config = manager.get_default_server()
    if config:
        return config
    raise ValueError("No default server configuration available")
