#!/usr/bin/env python3
"""
Security & Compliance Validation Script

Validates that all FedRAMP 140-3 security requirements are properly implemented:
- TLS 1.3 configuration
- FIPS 140-3 compliant cryptography
- Encryption at rest documentation
- Audit logging functionality
"""

import sys
import ssl
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.tls_config import create_ssl_context, create_client_ssl_context
from app.utils.crypto import FIPSCrypto
from app.middleware.audit import AuditLogger, AuditEvent


def validate_tls_configuration():
    """Validate TLS 1.3 configuration."""
    print("\n=== TLS 1.3 Configuration Validation ===")
    
    try:
        # Test server SSL context creation
        context = create_ssl_context()
        
        # Verify TLS version
        assert context.minimum_version == ssl.TLSVersion.TLSv1_3, \
            "Minimum TLS version should be 1.3"
        assert context.maximum_version == ssl.TLSVersion.TLSv1_3, \
            "Maximum TLS version should be 1.3"
        
        print("✓ TLS 1.3 server context created successfully")
        print(f"  - Minimum version: {context.minimum_version}")
        print(f"  - Maximum version: {context.maximum_version}")
        
        # Test client SSL context creation
        client_context = create_client_ssl_context()
        assert client_context.minimum_version == ssl.TLSVersion.TLSv1_3, \
            "Client minimum TLS version should be 1.3"
        
        print("✓ TLS 1.3 client context created successfully")
        
        # Verify configuration settings exist
        assert hasattr(settings, 'TLS_ENABLED'), "TLS_ENABLED setting missing"
        assert hasattr(settings, 'TLS_CERT_FILE'), "TLS_CERT_FILE setting missing"
        assert hasattr(settings, 'TLS_KEY_FILE'), "TLS_KEY_FILE setting missing"
        
        print("✓ TLS configuration settings present")
        print(f"  - TLS Enabled: {settings.TLS_ENABLED}")
        
        return True
        
    except Exception as e:
        print(f"✗ TLS configuration validation failed: {e}")
        return False


def validate_fips_cryptography():
    """Validate FIPS 140-3 compliant cryptography."""
    print("\n=== FIPS 140-3 Cryptography Validation ===")
    
    try:
        # Test AES-256-GCM encryption
        key = FIPSCrypto.generate_key(256)
        plaintext = b"Test data for FIPS validation"
        
        nonce, ciphertext = FIPSCrypto.encrypt_aes_gcm(plaintext, key)
        decrypted = FIPSCrypto.decrypt_aes_gcm(ciphertext, key, nonce)
        
        assert decrypted == plaintext, "AES-GCM encryption/decryption failed"
        assert len(key) == 32, "AES key should be 256 bits (32 bytes)"
        assert len(nonce) == 12, "GCM nonce should be 12 bytes"
        
        print("✓ AES-256-GCM encryption working correctly")
        print(f"  - Key size: {len(key) * 8} bits")
        print(f"  - Nonce size: {len(nonce)} bytes")
        
        # Test SHA-256 hashing
        data = b"Test data for hashing"
        hash_256 = FIPSCrypto.hash_sha256(data)
        assert len(hash_256) == 32, "SHA-256 hash should be 32 bytes"
        
        print("✓ SHA-256 hashing working correctly")
        print(f"  - Hash size: {len(hash_256)} bytes")
        
        # Test SHA-384 hashing
        hash_384 = FIPSCrypto.hash_sha384(data)
        assert len(hash_384) == 48, "SHA-384 hash should be 48 bytes"
        
        print("✓ SHA-384 hashing working correctly")
        
        # Test SHA-512 hashing
        hash_512 = FIPSCrypto.hash_sha512(data)
        assert len(hash_512) == 64, "SHA-512 hash should be 64 bytes"
        
        print("✓ SHA-512 hashing working correctly")
        
        # Test HMAC-SHA-256
        hmac_key = FIPSCrypto.generate_key(256)
        message = b"Test message for HMAC"
        hmac_tag = FIPSCrypto.hmac_sha256(hmac_key, message)
        assert len(hmac_tag) == 32, "HMAC-SHA-256 tag should be 32 bytes"
        
        print("✓ HMAC-SHA-256 working correctly")
        
        # Test RSA key generation
        private_pem, public_pem = FIPSCrypto.generate_rsa_keypair(2048)
        assert b"BEGIN PRIVATE KEY" in private_pem, "Invalid private key format"
        assert b"BEGIN PUBLIC KEY" in public_pem, "Invalid public key format"
        
        print("✓ RSA-2048 key generation working correctly")
        
        # Test RSA encryption/decryption
        test_data = b"Test RSA encryption"
        encrypted = FIPSCrypto.encrypt_rsa_oaep(test_data, public_pem)
        decrypted = FIPSCrypto.decrypt_rsa_oaep(encrypted, private_pem)
        assert decrypted == test_data, "RSA encryption/decryption failed"
        
        print("✓ RSA-OAEP encryption working correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ FIPS cryptography validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_encryption_at_rest():
    """Validate encryption at rest documentation."""
    print("\n=== Encryption at Rest Validation ===")
    
    try:
        # Check if documentation exists
        docs_path = Path(__file__).parent.parent.parent / "docs" / "opensearch-encryption.md"
        
        if not docs_path.exists():
            print("✗ OpenSearch encryption documentation not found")
            return False
        
        print("✓ OpenSearch encryption documentation exists")
        print(f"  - Location: {docs_path}")
        
        # Verify OpenSearch SSL settings exist
        assert hasattr(settings, 'OPENSEARCH_USE_SSL'), \
            "OPENSEARCH_USE_SSL setting missing"
        assert hasattr(settings, 'OPENSEARCH_VERIFY_CERTS'), \
            "OPENSEARCH_VERIFY_CERTS setting missing"
        
        print("✓ OpenSearch SSL configuration settings present")
        print(f"  - SSL Enabled: {settings.OPENSEARCH_USE_SSL}")
        print(f"  - Verify Certs: {settings.OPENSEARCH_VERIFY_CERTS}")
        
        return True
        
    except Exception as e:
        print(f"✗ Encryption at rest validation failed: {e}")
        return False


def validate_audit_logging():
    """Validate audit logging functionality."""
    print("\n=== Audit Logging Validation ===")
    
    try:
        # Test audit event creation
        event = AuditEvent(
            event_id="test-123",
            category=AuditEvent.SECURITY,
            action="test_action",
            outcome=AuditEvent.SUCCESS,
            user_id="test_user",
            resource="/test/resource",
            details={"test": "data"},
        )
        
        assert event.event_id == "test-123", "Event ID mismatch"
        assert event.category == AuditEvent.SECURITY, "Category mismatch"
        assert event.outcome == AuditEvent.SUCCESS, "Outcome mismatch"
        
        print("✓ Audit event creation working correctly")
        
        # Test event serialization
        event_dict = event.to_dict()
        assert "event_id" in event_dict, "Event dict missing event_id"
        assert "timestamp" in event_dict, "Event dict missing timestamp"
        assert "category" in event_dict, "Event dict missing category"
        
        print("✓ Audit event serialization working correctly")
        
        # Test JSON conversion
        event_json = event.to_json()
        assert isinstance(event_json, str), "Event JSON should be string"
        assert "test-123" in event_json, "Event JSON missing event_id"
        
        print("✓ Audit event JSON conversion working correctly")
        
        # Test audit logger methods
        AuditLogger.log_authentication(
            user_id="test_user",
            outcome=AuditEvent.SUCCESS,
            method="test",
            ip_address="127.0.0.1",
        )
        print("✓ Authentication audit logging working")
        
        AuditLogger.log_data_access(
            user_id="test_user",
            resource="/test/resource",
            action="read",
            outcome=AuditEvent.SUCCESS,
        )
        print("✓ Data access audit logging working")
        
        AuditLogger.log_security_event(
            user_id="test_user",
            action="security_test",
            outcome=AuditEvent.SUCCESS,
        )
        print("✓ Security event audit logging working")
        
        return True
        
    except Exception as e:
        print(f"✗ Audit logging validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all security compliance validations."""
    print("=" * 60)
    print("Security & Compliance Validation")
    print("FedRAMP 140-3 Requirements")
    print("=" * 60)
    
    results = {
        "TLS 1.3 Configuration": validate_tls_configuration(),
        "FIPS 140-3 Cryptography": validate_fips_cryptography(),
        "Encryption at Rest": validate_encryption_at_rest(),
        "Audit Logging": validate_audit_logging(),
    }
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All security compliance validations PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ Some security compliance validations FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
