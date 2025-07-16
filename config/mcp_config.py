"""
MCP server configuration management with YAML support
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env", {}),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30.0),
            retry_attempts=data.get("retry_attempts", 3),
            retry_delay=data.get("retry_delay", 1.0),
            description=data.get("description", "")
        )


class MCPConfigManager:
    """Manager for MCP server configurations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        project_root = Path(__file__).parent.parent
        return str(project_root / "config" / "mcp_servers.yaml")
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            logger.warning(f"MCP config file not found: {self.config_path}")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data or "servers" not in config_data:
                logger.warning("Invalid MCP config format, creating default")
                self._create_default_config()
                return
            
            self.servers = {}
            for server_data in config_data["servers"]:
                server_config = MCPServerConfig.from_dict(server_data)
                self.servers[server_config.name] = server_config
            
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "servers": [
                {
                    "name": "filesystem",
                    "command": "uvx",
                    "args": ["mcp-server-filesystem", "/tmp"],
                    "env": {},
                    "enabled": True,
                    "timeout": 30.0,
                    "retry_attempts": 3,
                    "retry_delay": 1.0,
                    "description": "Filesystem MCP server for file operations"
                },
                {
                    "name": "git",
                    "command": "uvx",
                    "args": ["mcp-server-git", "--repository", "."],
                    "env": {},
                    "enabled": False,
                    "timeout": 30.0,
                    "retry_attempts": 3,
                    "retry_delay": 1.0,
                    "description": "Git MCP server for version control operations"
                }
            ]
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            # Load the default config
            for server_data in default_config["servers"]:
                server_config = MCPServerConfig.from_dict(server_data)
                self.servers[server_config.name] = server_config
            
            logger.info(f"Created default MCP config at {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to create default MCP config: {e}")
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled server configurations"""
        return [server for server in self.servers.values() if server.enabled]
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name"""
        return self.servers.get(name)
    
    def add_server(self, server_config: MCPServerConfig) -> bool:
        """Add a new server configuration"""
        if server_config.name in self.servers:
            logger.warning(f"Server {server_config.name} already exists")
            return False
        
        self.servers[server_config.name] = server_config
        self._save_config()
        logger.info(f"Added MCP server: {server_config.name}")
        return True
    
    def update_server(self, name: str, server_config: MCPServerConfig) -> bool:
        """Update an existing server configuration"""
        if name not in self.servers:
            logger.warning(f"Server {name} not found")
            return False
        
        # Update name if changed
        if name != server_config.name:
            del self.servers[name]
        
        self.servers[server_config.name] = server_config
        self._save_config()
        logger.info(f"Updated MCP server: {server_config.name}")
        return True
    
    def remove_server(self, name: str) -> bool:
        """Remove a server configuration"""
        if name not in self.servers:
            logger.warning(f"Server {name} not found")
            return False
        
        del self.servers[name]
        self._save_config()
        logger.info(f"Removed MCP server: {name}")
        return True
    
    def enable_server(self, name: str) -> bool:
        """Enable a server"""
        server = self.servers.get(name)
        if not server:
            return False
        
        server.enabled = True
        self._save_config()
        logger.info(f"Enabled MCP server: {name}")
        return True
    
    def disable_server(self, name: str) -> bool:
        """Disable a server"""
        server = self.servers.get(name)
        if not server:
            return False
        
        server.enabled = False
        self._save_config()
        logger.info(f"Disabled MCP server: {name}")
        return True
    
    def _save_config(self):
        """Save configuration to YAML file"""
        config_data = {
            "servers": [server.to_dict() for server in self.servers.values()]
        }
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            logger.debug("MCP configuration saved")
        except Exception as e:
            logger.error(f"Failed to save MCP config: {e}")
    
    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
        logger.info("MCP configuration reloaded")
    
    def list_servers(self) -> List[str]:
        """Get list of all server names"""
        return list(self.servers.keys())
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        enabled_count = len(self.get_enabled_servers())
        total_count = len(self.servers)
        
        return {
            "config_path": self.config_path,
            "total_servers": total_count,
            "enabled_servers": enabled_count,
            "disabled_servers": total_count - enabled_count,
            "servers": {
                name: {
                    "enabled": server.enabled,
                    "description": server.description
                }
                for name, server in self.servers.items()
            }
        }


# Global configuration manager instance
_config_manager = None


def get_mcp_config_manager() -> MCPConfigManager:
    """Get or create the global MCP configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = MCPConfigManager()
    return _config_manager
