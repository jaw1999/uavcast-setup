"""System monitoring API routes."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/stats")
async def get_system_stats(request: Request):
    """Get current system statistics."""
    system_monitor = request.app.state.system_monitor
    return system_monitor.get_current_stats()


@router.get("/processes")
async def get_processes(request: Request, sort_by: str = "cpu"):
    """Get running processes."""
    system_monitor = request.app.state.system_monitor
    processes = await system_monitor.get_processes(sort_by=sort_by)
    return {"processes": processes}


@router.get("/disk-io")
async def get_disk_io(request: Request):
    """Get disk I/O statistics."""
    system_monitor = request.app.state.system_monitor
    disk_io = await system_monitor.get_disk_io()
    return disk_io
