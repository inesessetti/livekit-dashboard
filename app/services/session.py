"""Session management for server selection and user preferences"""

from typing import Optional
from fastapi import Request
from .server_config import get_server_config_manager


class SessionManager:
    """Manages user session data including server selection"""
    
    SESSION_SERVER_KEY = "selected_server_id"
    
    @staticmethod
    def get_selected_server_id(request: Request) -> Optional[str]:
        """Get the currently selected server ID from session"""
        return request.session.get(SessionManager.SESSION_SERVER_KEY)
    
    @staticmethod
    def set_selected_server_id(request: Request, server_id: str) -> bool:
        """Set the selected server ID in session"""
        manager = get_server_config_manager()
        
        # Validate server exists
        if not manager.get_server(server_id):
            return False
        
        request.session[SessionManager.SESSION_SERVER_KEY] = server_id
        return True
    
    @staticmethod
    def get_current_server_id(request: Request) -> Optional[str]:
        """Get current server ID (from session or None if not set)"""
        # Try to get from session first
        server_id = SessionManager.get_selected_server_id(request)
        
        if server_id:
            manager = get_server_config_manager()
            # Verify server still exists
            if manager.get_server(server_id):
                return server_id
        
        # Return None if no server is selected (will trigger server selection page)
        return None
    
    @staticmethod
    def clear_server_selection(request: Request):
        """Clear server selection from session"""
        if SessionManager.SESSION_SERVER_KEY in request.session:
            del request.session[SessionManager.SESSION_SERVER_KEY]
    
    @staticmethod
    def has_server_selection(request: Request) -> bool:
        """Check if user has selected a server"""
        return SessionManager.get_current_server_id(request) is not None


def get_current_server_id(request: Request) -> Optional[str]:
    """Convenience function to get current server ID"""
    return SessionManager.get_current_server_id(request)


def set_selected_server_id(request: Request, server_id: str) -> bool:
    """Convenience function to set selected server ID"""
    return SessionManager.set_selected_server_id(request, server_id)


def has_server_selection(request: Request) -> bool:
    """Convenience function to check if server is selected"""
    return SessionManager.has_server_selection(request)
