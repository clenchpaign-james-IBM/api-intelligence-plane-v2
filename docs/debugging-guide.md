# Debugging Guide: Python Backend in Docker

This guide explains how to debug the Python backend application running in Docker using VS Code's debugger.

## Prerequisites

- VS Code with Python extension installed
- Docker and Docker Compose installed
- Project dependencies installed in the container

## Setup Overview

The debugging setup consists of three components:

1. **debugpy** - Python debugging adapter added to [`backend/requirements.txt`](../backend/requirements.txt)
2. **docker-compose.debug.yml** - Docker Compose override file that enables debugging
3. **launch.json** - VS Code debugger configuration

## Quick Start

### 1. Start the Backend in Debug Mode

Stop any running containers first:

```bash
docker-compose down
```

Start the services with debug configuration:

```bash
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
```

The backend will start and **wait for the debugger to attach** before processing requests.

### 2. Attach the VS Code Debugger

1. Open the project in VS Code
2. Go to the **Run and Debug** panel (Ctrl+Shift+D / Cmd+Shift+D)
3. Select **"Python: Remote Attach (Docker)"** from the dropdown
4. Click the green **Start Debugging** button (F5)

You should see "Debugger attached" in the terminal, and the backend will start processing requests.

### 3. Set Breakpoints

- Open any Python file in the [`backend/app/`](../backend/app/) directory
- Click in the gutter (left of line numbers) to set breakpoints
- Breakpoints will be hit when the code executes

### 4. Debug Features

Once attached, you can:

- **Step through code** (F10 - Step Over, F11 - Step Into, Shift+F11 - Step Out)
- **Inspect variables** in the Variables panel
- **Evaluate expressions** in the Debug Console
- **View call stack** to understand execution flow
- **Set conditional breakpoints** (right-click on breakpoint)
- **Watch expressions** in the Watch panel

## Configuration Details

### Docker Compose Debug Override

The [`docker-compose.debug.yml`](../docker-compose.debug.yml) file:

- Exposes port **5678** for debugpy
- Installs debugpy in the container
- Starts the application with debugpy in **wait-for-client** mode
- Maintains hot-reload functionality with `--reload`

### VS Code Launch Configuration

The [`.vscode/launch.json`](../.vscode/launch.json) configures:

- **Remote attach** to localhost:5678
- **Path mappings** between local (`backend/`) and container (`/app`)
- **justMyCode: false** - allows debugging into libraries
- **subProcess: true** - debugs child processes (useful for uvicorn workers)

## Debugging Workflow

### Example: Debug an API Endpoint

1. Start services in debug mode:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
   ```

2. Attach debugger in VS Code (F5)

3. Set a breakpoint in [`backend/app/api/v1/gateways.py`](../backend/app/api/v1/gateways.py):
   ```python
   @router.get("/", response_model=List[GatewayResponse])
   async def list_gateways(
       gateway_service: GatewayService = Depends(get_gateway_service)
   ):
       # Set breakpoint here
       gateways = await gateway_service.list_gateways()
       return gateways
   ```

4. Make a request to the API:
   ```bash
   curl http://localhost:8000/api/v1/gateways
   ```

5. The debugger will pause at your breakpoint, allowing you to:
   - Inspect the `gateway_service` object
   - Step through the `list_gateways()` method
   - View the returned data

### Example: Debug Background Jobs

For debugging scheduled jobs or background tasks:

1. Set breakpoints in [`backend/app/services/discovery_service.py`](../backend/app/services/discovery_service.py)
2. The debugger will pause when the scheduler triggers the job
3. Inspect job state and execution flow

## Troubleshooting

### Debugger Won't Attach

**Problem**: "Connection refused" or timeout when attaching

**Solutions**:
- Ensure the backend container is running: `docker ps | grep aip-backend`
- Check port 5678 is exposed: `docker port aip-backend`
- Verify debugpy is installed: `docker exec aip-backend pip list | grep debugpy`
- Check container logs: `docker logs aip-backend`

### Breakpoints Not Hit

**Problem**: Breakpoints show as gray circles or aren't triggered

**Solutions**:
- Verify path mappings in [`launch.json`](../.vscode/launch.json) are correct
- Ensure you're editing the mounted volume files (not container copies)
- Check that the code path matches the breakpoint location
- Restart the debugger after code changes

### Performance Issues

**Problem**: Application runs slowly in debug mode

**Solutions**:
- Use conditional breakpoints to reduce pause frequency
- Set `justMyCode: true` in launch.json to skip library code
- Disable "Break on Exception" if not needed
- Use logging for high-frequency code paths instead of breakpoints

### Hot Reload Not Working

**Problem**: Code changes don't trigger reload

**Solutions**:
- Ensure `--reload` flag is in the docker-compose command
- Check that volumes are properly mounted in [`docker-compose.yml`](../docker-compose.yml)
- Verify file changes are saved (auto-save enabled)
- Some changes (like model changes) may require manual restart

## Normal Development Mode

To run without debugging (faster startup):

```bash
docker-compose up
```

This uses the standard configuration without debugpy overhead.

## Advanced Debugging

### Debug Specific Services

To debug only the backend while running other services normally:

```bash
# Start other services
docker-compose up opensearch frontend -d

# Start backend in debug mode
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up backend
```

### Debug with Environment Variables

Add environment variables to [`docker-compose.debug.yml`](../docker-compose.debug.yml):

```yaml
services:
  backend:
    environment:
      - DEBUGPY_ENABLED=true
      - LOG_LEVEL=DEBUG
      - CUSTOM_VAR=value
```

### Remote Debugging from Another Machine

To debug from a different machine on the network:

1. Modify [`docker-compose.debug.yml`](../docker-compose.debug.yml) to bind to all interfaces:
   ```yaml
   ports:
     - "5678:5678"  # Already configured
   ```

2. Update [`launch.json`](../.vscode/launch.json) with the Docker host IP:
   ```json
   "connect": {
     "host": "192.168.1.100",  // Docker host IP
     "port": 5678
   }
   ```

## Best Practices

1. **Use conditional breakpoints** for loops or high-frequency code
2. **Log important state** before debugging complex flows
3. **Clean up breakpoints** when done debugging
4. **Use the Debug Console** for quick expression evaluation
5. **Restart debugger** after significant code structure changes
6. **Monitor container resources** during long debug sessions

## Additional Resources

- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)
- [debugpy Documentation](https://github.com/microsoft/debugpy)
- [Docker Compose Override Files](https://docs.docker.com/compose/extends/)
- [FastAPI Debugging Guide](https://fastapi.tiangolo.com/tutorial/debugging/)

## Related Files

- [`backend/requirements.txt`](../backend/requirements.txt) - Python dependencies including debugpy
- [`docker-compose.yml`](../docker-compose.yml) - Base Docker Compose configuration
- [`docker-compose.debug.yml`](../docker-compose.debug.yml) - Debug mode override
- [`.vscode/launch.json`](../.vscode/launch.json) - VS Code debugger configuration
- [`backend/app/main.py`](../backend/app/main.py) - FastAPI application entry point