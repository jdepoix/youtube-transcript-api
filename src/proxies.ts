/**
 * Configuration for using a proxy server with HTTP/HTTPS requests.
 * This structure is compatible with Axios' proxy configuration.
 */
export interface ProxyConfig {
  /**
   * The proxy server host.
   */
  host: string;
  /**
   * The proxy server port.
   */
  port: number;
  /**
   * Optional. The username for proxy authentication.
   */
  auth?: {
    username: string;
    password?: string; // Password might be optional or handled differently
  };
  /**
   * Optional. The protocol for the proxy server (e.g., 'http', 'https', 'socks4', 'socks5').
   * Axios typically determines this from the proxy URL if provided as a string,
   * or defaults to 'http' if host/port are given.
   */
  protocol?: string;
}

// In Python, there's also GenericProxyConfig and WebshareProxyConfig.
// For now, a single ProxyConfig that aligns with Axios's needs is sufficient.
// If more complex proxy logic (like rotation from Webshare) is needed later,
// this can be expanded.
