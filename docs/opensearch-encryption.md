# OpenSearch Encryption at Rest Configuration

This document provides guidance on configuring encryption at rest for OpenSearch to meet FedRAMP 140-3 compliance requirements.

## Overview

Encryption at rest protects data stored on disk from unauthorized access. OpenSearch supports encryption at rest through:

1. **Node-to-node encryption** (already configured via TLS 1.3)
2. **Encryption at rest for indices** (filesystem-level or OpenSearch plugin)
3. **Snapshot encryption** (for backups)

## Configuration Options

### Option 1: Filesystem-Level Encryption (Recommended for Production)

Use operating system or cloud provider encryption:

#### AWS EBS Encryption
```yaml
# For AWS deployments
ebs_encryption: true
kms_key_id: "arn:aws:kms:region:account:key/key-id"
```

#### Linux LUKS Encryption
```bash
# Create encrypted volume
cryptsetup luksFormat /dev/sdb
cryptsetup luksOpen /dev/sdb opensearch_data

# Mount encrypted volume
mkfs.ext4 /dev/mapper/opensearch_data
mount /dev/mapper/opensearch_data /var/lib/opensearch
```

### Option 2: OpenSearch Encryption Plugin

For self-managed deployments, use the OpenSearch encryption-at-rest plugin:

#### Installation
```bash
# Install plugin
bin/opensearch-plugin install opensearch-encryption-at-rest

# Configure in opensearch.yml
plugins.security.encryption_at_rest.enabled: true
plugins.security.encryption_at_rest.key_provider_type: keystore
plugins.security.encryption_at_rest.keystore_path: /path/to/keystore.jks
plugins.security.encryption_at_rest.keystore_password: ${KEYSTORE_PASSWORD}
```

#### Generate Keystore
```bash
# Create keystore with AES-256 key
keytool -genseckey \
  -alias opensearch-encryption-key \
  -keyalg AES \
  -keysize 256 \
  -keystore /path/to/keystore.jks \
  -storetype JCEKS \
  -storepass ${KEYSTORE_PASSWORD}
```

### Option 3: Docker Volume Encryption

For Docker deployments:

```yaml
# docker-compose.yml
services:
  opensearch:
    image: opensearchproject/opensearch:latest
    volumes:
      - type: volume
        source: opensearch-data
        target: /usr/share/opensearch/data
        volume:
          driver: local
          driver_opts:
            type: "nfs"
            o: "addr=nfs-server,rw,encryption=aes256"
            device: ":/path/to/encrypted/volume"
```

## Kubernetes Configuration

For Kubernetes deployments with encrypted persistent volumes:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: opensearch-data
  annotations:
    volume.beta.kubernetes.io/storage-class: "encrypted-storage"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: encrypted-storage
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-storage
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:region:account:key/key-id"
```

## Environment Variables

Add to `.env`:

```bash
# OpenSearch Encryption at Rest
OPENSEARCH_ENCRYPTION_ENABLED=true
OPENSEARCH_KEYSTORE_PATH=/path/to/keystore.jks
OPENSEARCH_KEYSTORE_PASSWORD=your-secure-password

# For cloud providers
AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
AZURE_KEY_VAULT_URI=https://your-vault.vault.azure.net/
GCP_KMS_KEY_NAME=projects/PROJECT/locations/LOCATION/keyRings/RING/cryptoKeys/KEY
```

## Verification

### Check Encryption Status

```bash
# Check if encryption is enabled
curl -X GET "https://localhost:9200/_cluster/settings?include_defaults=true&pretty" \
  -u admin:admin \
  | grep encryption

# Verify encrypted indices
curl -X GET "https://localhost:9200/_cat/indices?v&h=index,store.size,pri.store.size" \
  -u admin:admin
```

### Test Encryption

```python
# Python script to verify encryption
from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=('admin', 'admin'),
    use_ssl=True,
    verify_certs=True,
)

# Create test index with encryption
index_body = {
    "settings": {
        "index": {
            "encryption": {
                "enabled": True
            }
        }
    }
}

client.indices.create(index='test-encrypted', body=index_body)
print("Encryption test successful")
```

## Backup Encryption

Ensure snapshots are also encrypted:

```bash
# Configure snapshot repository with encryption
curl -X PUT "https://localhost:9200/_snapshot/encrypted_backup" \
  -H 'Content-Type: application/json' \
  -u admin:admin \
  -d '{
    "type": "s3",
    "settings": {
      "bucket": "opensearch-backups",
      "region": "us-east-1",
      "server_side_encryption": true,
      "kms_key_id": "arn:aws:kms:region:account:key/key-id"
    }
  }'
```

## Compliance Checklist

- [ ] Encryption at rest enabled for all data volumes
- [ ] FIPS 140-3 approved encryption algorithms (AES-256)
- [ ] Secure key management (KMS or hardware security module)
- [ ] Encrypted backups and snapshots
- [ ] Key rotation policy implemented
- [ ] Access controls for encryption keys
- [ ] Audit logging for key access
- [ ] Regular encryption verification tests

## Key Rotation

Implement regular key rotation:

```bash
# Generate new key
keytool -genseckey \
  -alias opensearch-encryption-key-new \
  -keyalg AES \
  -keysize 256 \
  -keystore /path/to/keystore.jks \
  -storetype JCEKS

# Update OpenSearch configuration
# Restart OpenSearch nodes one by one
# Reindex data with new key
# Remove old key after verification
```

## Monitoring

Monitor encryption status:

```bash
# Check encryption metrics
curl -X GET "https://localhost:9200/_nodes/stats/indices?pretty" \
  -u admin:admin \
  | grep -A 5 "encryption"

# Alert on encryption failures
curl -X GET "https://localhost:9200/_cluster/health?pretty" \
  -u admin:admin
```

## Troubleshooting

### Common Issues

1. **Keystore not found**
   - Verify keystore path in configuration
   - Check file permissions (should be readable by OpenSearch user)

2. **Encryption performance impact**
   - Monitor CPU usage (encryption adds ~5-10% overhead)
   - Consider hardware acceleration (AES-NI)

3. **Key rotation failures**
   - Ensure sufficient disk space for reindexing
   - Verify new key is properly configured

## References

- [OpenSearch Security Plugin Documentation](https://opensearch.org/docs/latest/security-plugin/)
- [NIST FIPS 140-3 Standards](https://csrc.nist.gov/publications/detail/fips/140/3/final)
- [FedRAMP Encryption Requirements](https://www.fedramp.gov/)

## Support

For issues or questions:
- Check OpenSearch logs: `/var/log/opensearch/`
- Review security audit logs
- Contact security team for key management issues