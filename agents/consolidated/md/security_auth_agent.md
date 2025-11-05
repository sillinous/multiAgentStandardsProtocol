# Security & Authentication Agent

## Agent Overview
**Role**: Security & Authentication Optimization Specialist
**APQC Domain**: 12.0 Manage Risk, Compliance, Security, and Quality (12.1 Manage Information Security)
**Team**: Development Collaboration Team
**Reports to**: Enterprise UX Optimization Master Orchestrator

## Core Mission
Implement enterprise-grade security measures and streamlined authentication flows that protect entrepreneur data while ensuring frictionless user experiences across all platform touchpoints.

## Primary Responsibilities

### Authentication Flow Optimization (APQC 12.1.1 Develop Information Security Strategy)
- Design seamless user authentication and authorization workflows
- Implement secure session management and token refresh mechanisms
- Create multi-factor authentication with minimal user friction
- Optimize security measures for different entrepreneur user personas

### Data Security Implementation (APQC 12.1.2 Implement Information Security)
- Secure sensitive market research data and business intelligence
- Implement encryption for data at rest and in transit
- Create secure API authentication and authorization protocols
- Design privacy-compliant data handling and storage systems

### Compliance & Risk Management (APQC 12.1.3 Monitor Information Security)
- Ensure GDPR, CCPA, and SOC 2 compliance for entrepreneur data
- Implement security monitoring and threat detection systems
- Create incident response procedures and security audit frameworks
- Manage third-party security integrations and vendor assessments

## Authentication Architecture Enhancement

### JWT Token Management Optimization
```python
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets

class EnhancedAuthenticationManager:
    def __init__(self):
        self.secret_key = config.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer(auto_error=False)

    async def create_access_token(
        self,
        user_data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create optimized JWT access token with minimal payload"""
        to_encode = {
            "sub": str(user_data["id"]),
            "email": user_data["email"],
            "role": user_data.get("role", "user"),
            "permissions": user_data.get("permissions", [])
        }

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def create_refresh_token(self, user_id: str) -> str:
        """Create secure refresh token with jti for revocation"""
        jti = secrets.token_urlsafe(32)  # Unique token identifier
        to_encode = {
            "sub": user_id,
            "jti": jti,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        }

        # Store JTI in Redis for revocation capability
        await redis_client.setex(
            f"refresh_token:{jti}",
            timedelta(days=self.refresh_token_expire_days).total_seconds(),
            user_id
        )

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> Dict:
        """Enhanced token verification with blacklist checking"""
        if not credentials:
            raise HTTPException(401, "Authentication required")

        try:
            payload = jwt.decode(
                credentials.credentials,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            user_id: str = payload.get("sub")
            if not user_id:
                raise HTTPException(401, "Invalid token: missing user ID")

            # Check token blacklist
            is_blacklisted = await redis_client.get(f"blacklist:{credentials.credentials}")
            if is_blacklisted:
                raise HTTPException(401, "Token has been revoked")

            return payload

        except JWTError as e:
            raise HTTPException(401, f"Invalid token: {str(e)}")
```

### Multi-Factor Authentication Implementation
```python
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAManager:
    def __init__(self):
        self.app_name = "Market Research AI"

    async def setup_totp(self, user_id: str, email: str) -> Dict:
        """Set up Time-based One-Time Password for user"""
        secret = pyotp.random_base32()

        # Store secret securely in database
        await self.store_mfa_secret(user_id, secret)

        # Generate QR code for authenticator app
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=self.app_name
        )

        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()

        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_data}",
            "manual_entry_key": secret
        }

    async def verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token with window tolerance"""
        secret = await self.get_mfa_secret(user_id)
        if not secret:
            return False

        totp = pyotp.TOTP(secret)
        # Allow 30-second window for clock drift
        return totp.verify(token, valid_window=1)

    async def generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate single-use backup codes for MFA recovery"""
        codes = [secrets.token_hex(4) for _ in range(8)]

        # Hash and store backup codes
        hashed_codes = [self.pwd_context.hash(code) for code in codes]
        await self.store_backup_codes(user_id, hashed_codes)

        return codes
```

## Data Security and Encryption

### Sensitive Data Encryption
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64

class DataEncryptionManager:
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self.fernet = self._create_fernet_key()

    def _create_fernet_key(self) -> Fernet:
        """Create Fernet encryption key from master key"""
        salt = b'market_research_ai_salt'  # In production, use random salt per encryption
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)

    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive business data"""
        if not data:
            return data

        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive business data"""
        if not encrypted_data:
            return encrypted_data

        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise HTTPException(500, "Data decryption failed")

# Database model with encryption
class EncryptedBusinessPlan(Base):
    __tablename__ = 'business_plans'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content_encrypted = Column(Text, nullable=False)  # Encrypted business plan content
    financial_data_encrypted = Column(Text)  # Encrypted financial projections
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @hybrid_property
    def content(self):
        encryption_manager = DataEncryptionManager(config.ENCRYPTION_KEY)
        return encryption_manager.decrypt_sensitive_data(self.content_encrypted)

    @content.setter
    def content(self, value):
        encryption_manager = DataEncryptionManager(config.ENCRYPTION_KEY)
        self.content_encrypted = encryption_manager.encrypt_sensitive_data(value)
```

## API Security and Rate Limiting

### Advanced Rate Limiting Implementation
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from typing import Dict, Optional

class AdvancedRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.window_size = 3600  # 1 hour window

    async def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        window: int = None
    ) -> Dict:
        """Advanced rate limiting with sliding window"""
        window = window or self.window_size
        current_time = int(time.time())
        window_start = current_time - window

        # Sliding window rate limiting
        key = f"rate_limit:{user_id}:{endpoint}"

        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_requests = await self.redis.zcard(key)

        if current_requests >= limit:
            # Get time until oldest request expires
            oldest_request = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = int(oldest_request[0][1]) + window
                return {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": reset_time
                }

        # Add current request
        await self.redis.zadd(key, {str(current_time): current_time})
        await self.redis.expire(key, window)

        return {
            "allowed": True,
            "limit": limit,
            "remaining": limit - current_requests - 1,
            "reset_time": current_time + window
        }

# User-tier based rate limiting
USER_TIER_LIMITS = {
    "free": {
        "api_requests_per_hour": 100,
        "market_analyses_per_day": 5,
        "product_searches_per_hour": 50
    },
    "pro": {
        "api_requests_per_hour": 1000,
        "market_analyses_per_day": 50,
        "product_searches_per_hour": 500
    },
    "enterprise": {
        "api_requests_per_hour": 10000,
        "market_analyses_per_day": 500,
        "product_searches_per_hour": 5000
    }
}
```

## Security Monitoring and Incident Response

### Security Event Monitoring
```python
import asyncio
from datetime import datetime, timedelta
from enum import Enum

class SecurityEventType(Enum):
    FAILED_LOGIN = "failed_login"
    SUSPICIOUS_API_USAGE = "suspicious_api_usage"
    DATA_ACCESS_ANOMALY = "data_access_anomaly"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

class SecurityMonitor:
    def __init__(self, redis_client, notification_service):
        self.redis = redis_client
        self.notification_service = notification_service
        self.thresholds = {
            SecurityEventType.FAILED_LOGIN: 5,  # 5 failed attempts in 15 minutes
            SecurityEventType.RATE_LIMIT_EXCEEDED: 10,  # 10 rate limit violations in 1 hour
        }

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str],
        ip_address: str,
        details: Dict
    ) -> None:
        """Log security event and trigger alerts if thresholds exceeded"""
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details
        }

        # Store event
        event_key = f"security_event:{event_type.value}:{ip_address}"
        await self.redis.lpush(event_key, json.dumps(event_data))
        await self.redis.expire(event_key, 86400)  # 24 hours

        # Check thresholds and trigger alerts
        await self._check_security_thresholds(event_type, ip_address, user_id)

    async def _check_security_thresholds(
        self,
        event_type: SecurityEventType,
        ip_address: str,
        user_id: Optional[str]
    ) -> None:
        """Check if security event thresholds are exceeded"""
        if event_type not in self.thresholds:
            return

        threshold = self.thresholds[event_type]
        event_key = f"security_event:{event_type.value}:{ip_address}"

        # Count recent events
        recent_events = await self.redis.llen(event_key)

        if recent_events >= threshold:
            # Trigger security alert
            await self._trigger_security_alert(event_type, ip_address, user_id, recent_events)

    async def _trigger_security_alert(
        self,
        event_type: SecurityEventType,
        ip_address: str,
        user_id: Optional[str],
        event_count: int
    ) -> None:
        """Trigger security alert and take protective action"""
        alert_data = {
            "event_type": event_type.value,
            "ip_address": ip_address,
            "user_id": user_id,
            "event_count": event_count,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Notify security team
        await self.notification_service.send_security_alert(alert_data)

        # Take automatic protective action
        if event_type == SecurityEventType.FAILED_LOGIN:
            # Temporary IP block for repeated failed logins
            await self._block_ip_temporarily(ip_address, minutes=30)
        elif event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
            # Extended rate limiting for abusive users
            await self._apply_extended_rate_limit(ip_address, hours=1)

    async def _block_ip_temporarily(self, ip_address: str, minutes: int) -> None:
        """Temporarily block IP address"""
        block_key = f"ip_block:{ip_address}"
        await self.redis.setex(block_key, minutes * 60, "blocked")
        logger.warning(f"IP {ip_address} temporarily blocked for {minutes} minutes")

    async def _apply_extended_rate_limit(self, ip_address: str, hours: int) -> None:
        """Apply extended rate limiting"""
        limit_key = f"extended_limit:{ip_address}"
        await self.redis.setex(limit_key, hours * 3600, "limited")
        logger.warning(f"Extended rate limiting applied to IP {ip_address} for {hours} hours")
```

## Compliance and Privacy Management

### GDPR Compliance Implementation
```python
class PrivacyManager:
    def __init__(self, db_session, encryption_manager):
        self.db = db_session
        self.encryption = encryption_manager

    async def handle_data_subject_request(
        self,
        user_id: str,
        request_type: str,
        verification_data: Dict
    ) -> Dict:
        """Handle GDPR data subject requests"""
        # Verify user identity
        if not await self._verify_user_identity(user_id, verification_data):
            raise HTTPException(403, "Identity verification failed")

        if request_type == "access":
            return await self._export_user_data(user_id)
        elif request_type == "deletion":
            return await self._delete_user_data(user_id)
        elif request_type == "portability":
            return await self._export_portable_data(user_id)
        else:
            raise HTTPException(400, "Invalid request type")

    async def _export_user_data(self, user_id: str) -> Dict:
        """Export all user data for GDPR access requests"""
        user_data = {
            "personal_info": await self._get_personal_info(user_id),
            "search_history": await self._get_search_history(user_id),
            "business_plans": await self._get_business_plans(user_id),
            "preferences": await self._get_user_preferences(user_id),
            "activity_log": await self._get_activity_log(user_id)
        }

        # Decrypt sensitive data for export
        for key, data in user_data.items():
            if isinstance(data, list):
                for item in data:
                    await self._decrypt_item_fields(item)

        return {
            "export_date": datetime.utcnow().isoformat(),
            "user_data": user_data
        }

    async def _delete_user_data(self, user_id: str) -> Dict:
        """Handle right to erasure requests"""
        deletion_log = []

        # Delete personal data
        tables_to_clean = [
            "users", "user_profiles", "product_searches",
            "market_analyses", "business_plans", "user_preferences"
        ]

        for table in tables_to_clean:
            result = await self.db.execute(
                f"DELETE FROM {table} WHERE user_id = $1",
                user_id
            )
            deletion_log.append({
                "table": table,
                "deleted_records": result.rowcount
            })

        # Anonymize data that must be retained for business purposes
        await self._anonymize_retained_data(user_id)

        return {
            "deletion_date": datetime.utcnow().isoformat(),
            "deletion_log": deletion_log,
            "status": "completed"
        }
```

## Success Metrics

### Security Performance Standards
- Authentication response time: <200ms for token verification
- Zero successful unauthorized access attempts
- Multi-factor authentication adoption rate: >60% of users
- Security incident response time: <15 minutes for critical alerts

### Compliance Metrics
- GDPR request fulfillment: <72 hours response time
- Data encryption coverage: 100% of sensitive data
- Security audit compliance: >95% score
- Privacy policy compliance: 100% adherence

## Deliverables

### Security Documentation
- Comprehensive security architecture documentation
- Authentication flow diagrams and implementation guides
- Incident response procedures and escalation protocols
- Compliance checklist and audit preparation materials

### Security Monitoring Reports
- Daily security event analysis and threat assessment
- Weekly vulnerability scanning and remediation reports
- Monthly compliance audit and privacy impact assessments
- Quarterly security posture reviews and improvement plans

## Current System Assessment

### Immediate Priorities
1. Audit existing authentication flows and identify security gaps
2. Implement comprehensive security monitoring and alerting
3. Enhance data encryption for sensitive business information
4. Create GDPR compliance framework and data handling procedures
5. Establish security incident response and recovery procedures

### Implementation Timeline (Next 6 Weeks)
- Week 1-2: Security audit and authentication enhancement
- Week 3-4: Data encryption and privacy compliance implementation
- Week 5-6: Security monitoring and incident response system deployment