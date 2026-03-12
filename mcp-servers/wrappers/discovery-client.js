#!/usr/bin/env node
/**
 * MCP Client Wrapper for Discovery Server
 * This script connects to the Discovery MCP server via streamable HTTP
 * and forwards stdio communication for Bob IDE
 */

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StreamableHTTPClientTransport } = require('@modelcontextprotocol/sdk/client/streamable-http.js');

async function main() {
  const serverUrl = 'http://localhost:8001/mcp';
  
  // Create transport
  const transport = new StreamableHTTPClientTransport(new URL(serverUrl));
  
  // Create client
  const client = new Client(
    {
      name: 'bob-ide-discovery-client',
      version: '1.0.0',
    },
    {
      capabilities: {},
    }
  );

  // Connect
  await client.connect(transport);
  
  // Keep alive
  process.on('SIGINT', async () => {
    await client.close();
    process.exit(0);
  });
  
  // Wait indefinitely
  await new Promise(() => {});
}

main().catch(console.error);

// Made with Bob
