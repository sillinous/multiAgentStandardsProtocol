//! Protocol and communication standards

use serde::{Deserialize, Serialize};

/// Supported communication protocols
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum Protocol {
    /// Agent-to-Agent Protocol (Google/Linux Foundation)
    A2A,

    /// Model Context Protocol (Anthropic)
    MCP,

    /// Agent Name Service (emerging)
    ANS,

    /// HTTP/REST (traditional)
    HTTP,

    /// WebSocket (real-time bidirectional)
    WebSocket,

    /// Internal message bus
    Internal,
}

impl std::fmt::Display for Protocol {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Protocol::A2A => write!(f, "a2a"),
            Protocol::MCP => write!(f, "mcp"),
            Protocol::ANS => write!(f, "ans"),
            Protocol::HTTP => write!(f, "http"),
            Protocol::WebSocket => write!(f, "websocket"),
            Protocol::Internal => write!(f, "internal"),
        }
    }
}

/// Protocol version information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProtocolVersion {
    /// Protocol name
    pub protocol: Protocol,

    /// Major version number
    pub major: u32,

    /// Minor version number
    pub minor: u32,

    /// Patch version number
    pub patch: u32,

    /// Optional prerelease identifier
    pub prerelease: Option<String>,
}

impl ProtocolVersion {
    /// Create a new protocol version
    pub fn new(protocol: Protocol, major: u32, minor: u32, patch: u32) -> Self {
        Self {
            protocol,
            major,
            minor,
            patch,
            prerelease: None,
        }
    }

    /// A2A protocol version 1.0
    pub fn a2a_v1() -> Self {
        Self::new(Protocol::A2A, 1, 0, 0)
    }

    /// MCP protocol version 1.0
    pub fn mcp_v1() -> Self {
        Self::new(Protocol::MCP, 1, 0, 0)
    }

    /// HTTP version 1.1
    pub fn http_v1() -> Self {
        Self::new(Protocol::HTTP, 1, 1, 0)
    }

    /// WebSocket version 13 (RFC 6455)
    pub fn websocket_v13() -> Self {
        Self::new(Protocol::WebSocket, 13, 0, 0)
    }

    /// Get version string (e.g., "1.0.0")
    pub fn to_string(&self) -> String {
        if let Some(pre) = &self.prerelease {
            format!("{}.{}.{}-{}", self.major, self.minor, self.patch, pre)
        } else {
            format!("{}.{}.{}", self.major, self.minor, self.patch)
        }
    }

    /// Check if this version is compatible with another
    pub fn is_compatible_with(&self, other: &ProtocolVersion) -> bool {
        // Same protocol and major version = compatible
        self.protocol == other.protocol && self.major == other.major
    }
}

/// Encryption method for protocol communication
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub enum EncryptionMethod {
    /// TLS 1.2
    TLS12,

    /// TLS 1.3
    TLS13,

    /// End-to-end encryption with public key
    E2EPublicKey,

    /// No encryption (development only)
    None,
}

/// Authentication method for protocol communication
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum AuthenticationMethod {
    /// OAuth 2.1
    OAuth2,

    /// API key
    ApiKey,

    /// Bearer token
    Bearer(String),

    /// Mutual TLS
    MutualTLS,

    /// Decentralized Identifier (DID)
    DID(String),

    /// None (for internal communication)
    None,
}

/// Configuration for protocol communication
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProtocolConfig {
    /// Protocol to use
    pub protocol: Protocol,

    /// Protocol version
    pub version: ProtocolVersion,

    /// Encryption method
    pub encryption: EncryptionMethod,

    /// Authentication method
    pub auth: AuthenticationMethod,

    /// Connection timeout in seconds
    pub timeout_secs: u64,

    /// Maximum message size in bytes
    pub max_message_size: usize,

    /// Whether to enable compression
    pub enable_compression: bool,

    /// Maximum retries for failed messages
    pub max_retries: u32,
}

impl Default for ProtocolConfig {
    fn default() -> Self {
        Self {
            protocol: Protocol::HTTP,
            version: ProtocolVersion::http_v1(),
            encryption: EncryptionMethod::TLS13,
            auth: AuthenticationMethod::Bearer("".to_string()),
            timeout_secs: 30,
            max_message_size: 10 * 1024 * 1024, // 10MB
            enable_compression: true,
            max_retries: 3,
        }
    }
}

impl ProtocolConfig {
    /// Create a config for A2A protocol
    pub fn a2a() -> Self {
        Self {
            protocol: Protocol::A2A,
            version: ProtocolVersion::a2a_v1(),
            encryption: EncryptionMethod::TLS13,
            auth: AuthenticationMethod::OAuth2,
            timeout_secs: 300, // Longer for long-running tasks
            max_message_size: 50 * 1024 * 1024, // 50MB
            enable_compression: true,
            max_retries: 3,
        }
    }

    /// Create a config for MCP protocol
    pub fn mcp() -> Self {
        Self {
            protocol: Protocol::MCP,
            version: ProtocolVersion::mcp_v1(),
            encryption: EncryptionMethod::TLS13,
            auth: AuthenticationMethod::ApiKey,
            timeout_secs: 60,
            max_message_size: 10 * 1024 * 1024,
            enable_compression: true,
            max_retries: 3,
        }
    }

    /// Create a config for WebSocket
    pub fn websocket() -> Self {
        Self {
            protocol: Protocol::WebSocket,
            version: ProtocolVersion::websocket_v13(),
            encryption: EncryptionMethod::TLS13,
            auth: AuthenticationMethod::Bearer("".to_string()),
            timeout_secs: 0, // No timeout for persistent connections
            max_message_size: 100 * 1024 * 1024,
            enable_compression: true,
            max_retries: 0, // WebSocket handles retries differently
        }
    }

    /// Create a config for internal communication
    pub fn internal() -> Self {
        Self {
            protocol: Protocol::Internal,
            version: ProtocolVersion::new(Protocol::Internal, 1, 0, 0),
            encryption: EncryptionMethod::None,
            auth: AuthenticationMethod::None,
            timeout_secs: 10,
            max_message_size: 100 * 1024 * 1024,
            enable_compression: false,
            max_retries: 3,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_protocol_version() {
        let version = ProtocolVersion::a2a_v1();
        assert_eq!(version.to_string(), "1.0.0");
    }

    #[test]
    fn test_protocol_compatibility() {
        let v1 = ProtocolVersion::a2a_v1();
        let v1_1 = ProtocolVersion::new(Protocol::A2A, 1, 1, 0);
        let v2 = ProtocolVersion::new(Protocol::A2A, 2, 0, 0);

        assert!(v1.is_compatible_with(&v1_1));
        assert!(!v1.is_compatible_with(&v2));
    }

    #[test]
    fn test_protocol_configs() {
        let a2a_config = ProtocolConfig::a2a();
        assert_eq!(a2a_config.protocol, Protocol::A2A);
        assert_eq!(a2a_config.timeout_secs, 300);

        let mcp_config = ProtocolConfig::mcp();
        assert_eq!(mcp_config.protocol, Protocol::MCP);
    }
}
