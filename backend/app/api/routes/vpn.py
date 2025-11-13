"""VPN API routes."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/vpn", tags=["vpn"])


class ZeroTierConfig(BaseModel):
    network_id: str


class TailscaleConfig(BaseModel):
    auth_key: str


class WireGuardConfig(BaseModel):
    config_content: str


@router.post("/zerotier/connect")
async def connect_zerotier(config: ZeroTierConfig, request: Request):
    """Connect to ZeroTier network."""
    vpn_manager = request.app.state.vpn_manager
    result = await vpn_manager.configure_zerotier(config.network_id)
    return result


@router.post("/tailscale/connect")
async def connect_tailscale(config: TailscaleConfig, request: Request):
    """Connect to Tailscale."""
    vpn_manager = request.app.state.vpn_manager
    result = await vpn_manager.configure_tailscale(config.auth_key)
    return result


@router.post("/wireguard/connect")
async def connect_wireguard(config: WireGuardConfig, request: Request):
    """Connect to WireGuard."""
    vpn_manager = request.app.state.vpn_manager
    result = await vpn_manager.configure_wireguard(config.config_content)
    return result


@router.post("/disconnect")
async def disconnect_vpn(request: Request):
    """Disconnect from VPN."""
    vpn_manager = request.app.state.vpn_manager
    result = await vpn_manager.disconnect()
    return result


@router.get("/status")
async def get_vpn_status(request: Request):
    """Get VPN status."""
    vpn_manager = request.app.state.vpn_manager
    return vpn_manager.get_status()
