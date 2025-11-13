"""Network and modem API routes."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/interfaces")
async def get_network_interfaces(request: Request):
    """Get all network interfaces."""
    # Create network manager on demand
    from app.services.network_manager import NetworkManager

    network_manager = NetworkManager()
    interfaces = await network_manager.get_interfaces()
    return {"interfaces": interfaces}


@router.get("/modem")
async def detect_modem(request: Request):
    """Detect LTE/4G modem."""
    from app.services.network_manager import NetworkManager

    network_manager = NetworkManager()
    modem = await network_manager.detect_modem()
    return {"modem": modem}


@router.get("/modem/signal")
async def get_signal_strength(request: Request):
    """Get cellular signal strength."""
    from app.services.network_manager import NetworkManager

    network_manager = NetworkManager()

    # Detect modem first
    await network_manager.detect_modem()

    # Get signal
    signal = await network_manager.get_signal_strength()
    return {"signal": signal}


@router.get("/status")
async def get_connection_status(request: Request):
    """Get network connection status."""
    from app.services.network_manager import NetworkManager

    network_manager = NetworkManager()
    status = await network_manager.get_connection_status()
    return status


@router.get("/test")
async def test_connectivity(request: Request, host: str = "8.8.8.8"):
    """Test internet connectivity."""
    from app.services.network_manager import NetworkManager

    network_manager = NetworkManager()
    result = await network_manager.test_connectivity(host)
    return result
