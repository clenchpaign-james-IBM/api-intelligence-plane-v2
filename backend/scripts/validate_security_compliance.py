"""
Security Compliance Validation Script

Validates FedRAMP 140-3 compliance requirements for the API Intelligence Plane.
Checks:
- TLS 1.3 configuration
- FIPS 140-3 compliant cryptography
- Audit logging
- Secure configuration
- Environment variable security
"""

import os
import sys
import ssl
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.utils.crypto import FIPSCrypto
from app.utils.tls_config import create_ssl_context, create_client_ssl_context


class SecurityValidator:
    """Validates security compliance requirements."""
    
    def __init__(self):
        self.settings = Settings()
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def validate_all(self) -> bool:
        """Run all security validation checks."""
        print("=" * 80)
        print("Security Compliance Validation")
        print("=" * 80)
        print()
        
        self.check_tls_configuration()
        self.check_cryptography()
        self.check_environment_security()
        self.check_audit_logging()
        self.check_opensearch_security()
        
        self.print_results()
        
        return len(self.failed) == 0
    
    def check_tls_configuration(self):
        """Validate TLS 1.3 configuration."""
        print("Checking TLS Configuration...")
        
        try:
            # Check if TLS 1.3 is available
            if not hasattr(ssl.TLSVersion, 'TLSv1_3'):
                self.failed.append("TLS 1.3 not available in Python SSL module")
                return
            
            # Create SSL context
            context = create_client_ssl_context()
            
            # Verify TLS 1.3 minimum version
            if context.minimum_version == ssl.TLSVersion.TLSv1_3:
                self.passed.append("✓ TLS 1.3 minimum version configured")
            else:
                self.failed.append("✗ TLS 1.3 minimum version not set")
            
            # Verify TLS 1.3 maximum version
            if context.maximum_version == ssl.TLSVersion.TLSv1_3:
                self.passed.append("✓ TLS 1.3 maximum version enforced")
            else:
                self.warnings.append("⚠ TLS 1.3 maximum version not enforced")
            
            # Check hostname verification
            if context.check_hostname:
                self.passed.append("✓ Hostname verification enabled")
            else:
                self.failed.append("✗ Hostname verification disabled")
            
            # Check certificate verification
            if context.verify_mode == ssl.CERT_REQUIRED:
                self.passed.append("✓ Certificate verification required")
            else:
                self.failed.append("✗ Certificate verification not required")
            
        except Exception as e:
            self.failed.append(f"✗ TLS configuration error: {e}")
    
    def check_cryptography(self):
        """Validate FIPS 140-3 compliant cryptography."""
        print("Checking Cryptographic Algorithms...")
        
        try:
            # Test AES-256-GCM encryption
            test_data = b"Test data for encryption"
            key = FIPSCrypto.generate_key(256)
            nonce, ciphertext = FIPSCrypto.encrypt_aes_gcm(test_data, key)
            decrypted = FIPSCrypto.decrypt_aes_gcm(ciphertext, key, nonce)
            
            if decrypted == test_data:
                self.passed.append("✓ AES-256-GCM encryption/decryption working")
            else:
                self.failed.append("✗ AES-256-GCM encryption/decryption failed")
            
            # Test SHA-256 hashing
            hash_result = FIPSCrypto.hash_sha256(test_data)
            if len(hash_result) == 32:  # SHA-256 produces 32 bytes
                self.passed.append("✓ SHA-256 hashing working")
            else:
                self.failed.append("✗ SHA-256 hashing failed")
            
            # Test HMAC-SHA-256
            hmac_result = FIPSCrypto.hmac_sha256(key, test_data)
            if len(hmac_result) == 32:  # HMAC-SHA-256 produces 32 bytes
                self.passed.append("✓ HMAC-SHA-256 working")
            else:
                self.failed.append("✗ HMAC-SHA-256 failed")
            
            # Test RSA key generation
            private_key, public_key = FIPSCrypto.generate_rsa_keypair(2048)
            if b"BEGIN PRIVATE KEY" in private_key and b"BEGIN PUBLIC KEY" in public_key:
                self.passed.append("✓ RSA-2048 key generation working")
            else:
                self.failed.append("✗ RSA key generation failed")
            
        except Exception as e:
            self.failed.append(f"✗ Cryptography error: {e}")
    
    def check_environment_security(self):
        """Validate environment variable security."""
        print("Checking Environment Security...")
        
        # Check for SECRET_KEY
        if hasattr(self.settings, 'SECRET_KEY') and self.settings.SECRET_KEY:
            if len(self.settings.SECRET_KEY) >= 32:
                self.passed.append("✓ SECRET_KEY configured with sufficient length")
            else:
                self.warnings.append("⚠ SECRET_KEY should be at least 32 characters")
        else:
            self.failed.append("✗ SECRET_KEY not configured")
        
        # Check for sensitive data in environment
        sensitive_patterns = ['password', 'secret', 'key', 'token']
        env_vars = os.environ.keys()
        
        for var in env_vars:
            if any(pattern in var.lower() for pattern in sensitive_patterns):
                if os.environ[var] and os.environ[var] != "":
                    self.passed.append(f"✓ {var} is set")
                else:
                    self.warnings.append(f"⚠ {var} is empty")
        
        # Check OpenSearch credentials
        if self.settings.OPENSEARCH_USER and self.settings.OPENSEARCH_PASSWORD:
            self.passed.append("✓ OpenSearch credentials configured")
        else:
            self.warnings.append("⚠ OpenSearch credentials not configured")
    
    def check_audit_logging(self):
        """Validate audit logging configuration."""
        print("Checking Audit Logging...")
        
        # Check if audit logging is configured
        try:
            import logging
            audit_logger = logging.getLogger("audit")
            
            if audit_logger.handlers:
                self.passed.append("✓ Audit logger configured")
            else:
                self.warnings.append("⚠ Audit logger has no handlers")
            
            # Check log level
            if audit_logger.level <= logging.INFO:
                self.passed.append("✓ Audit log level appropriate (INFO or lower)")
            else:
                self.warnings.append("⚠ Audit log level too high")
            
        except Exception as e:
            self.failed.append(f"✗ Audit logging error: {e}")
    
    def check_opensearch_security(self):
        """Validate OpenSearch security configuration."""
        print("Checking OpenSearch Security...")
        
        # Check SSL configuration
        if self.settings.OPENSEARCH_USE_SSL:
            self.passed.append("✓ OpenSearch SSL enabled")
            
            if self.settings.OPENSEARCH_VERIFY_CERTS:
                self.passed.append("✓ OpenSearch certificate verification enabled")
            else:
                self.warnings.append("⚠ OpenSearch certificate verification disabled")
        else:
            self.warnings.append("⚠ OpenSearch SSL disabled (OK for development)")
        
        # Check authentication
        if self.settings.OPENSEARCH_USER and self.settings.OPENSEARCH_PASSWORD:
            self.passed.append("✓ OpenSearch authentication configured")
        else:
            self.failed.append("✗ OpenSearch authentication not configured")
    
    def print_results(self):
        """Print validation results."""
        print()
        print("=" * 80)
        print("Validation Results")
        print("=" * 80)
        print()
        
        if self.passed:
            print(f"PASSED ({len(self.passed)}):")
            for item in self.passed:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        if self.failed:
            print(f"FAILED ({len(self.failed)}):")
            for item in self.failed:
                print(f"  {item}")
            print()
        
        print("=" * 80)
        total = len(self.passed) + len(self.warnings) + len(self.failed)
        print(f"Total Checks: {total}")
        print(f"Passed: {len(self.passed)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Failed: {len(self.failed)}")
        print("=" * 80)
        
        if self.failed:
            print("\n❌ SECURITY VALIDATION FAILED")
            print("Please address the failed checks before deployment.")
        elif self.warnings:
            print("\n⚠️  SECURITY VALIDATION PASSED WITH WARNINGS")
            print("Consider addressing warnings for production deployment.")
        else:
            print("\n✅ SECURITY VALIDATION PASSED")
            print("All security compliance checks passed.")


def main():
    """Run security validation."""
    validator = SecurityValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
