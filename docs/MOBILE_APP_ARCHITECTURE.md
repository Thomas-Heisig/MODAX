# MODAX Mobile App Architecture

**Last Updated:** 2025-12-09  
**Status:** Design Phase  
**Version:** 1.0  
**Target Platforms:** iOS 14+, Android 8.0+

## Overview

The MODAX Mobile App provides real-time monitoring and alert capabilities for industrial control systems on-the-go. The app is designed as a **monitoring-only** interface with no direct control capabilities to maintain safety.

## Architecture

### Technology Stack

#### Cross-Platform Framework
- **React Native** (recommended) or **Flutter**
  - Single codebase for iOS and Android
  - Native performance
  - Large ecosystem and community support

#### Backend Communication
- **REST API** for data fetching
- **WebSocket/SSE** for real-time updates
- **Push Notifications** for critical alerts

#### State Management
- **Redux** (React Native) or **Provider/Bloc** (Flutter)
- Offline-first architecture with local caching

#### Local Storage
- **SQLite** for offline data caching
- **Secure Storage** for authentication tokens

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile App (iOS/Android)              │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐     │
│  │ Dashboard  │  │  Devices   │  │   Alerts     │     │
│  │   View     │  │   View     │  │    View      │     │
│  └────────────┘  └────────────┘  └──────────────┘     │
│         │               │                  │            │
│  ┌──────▼───────────────▼──────────────────▼──────┐   │
│  │           State Management (Redux/Bloc)         │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │            Data Layer                            │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌───────────┐  │   │
│  │  │ API Client  │  │ WebSocket│  │  SQLite   │  │   │
│  │  │  (REST)     │  │  Client  │  │   Cache   │  │   │
│  │  └─────────────┘  └──────────┘  └───────────┘  │   │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              MODAX Backend Services                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Control API  │  │  AI API      │  │   Push       │  │
│  │ (Port 8000)  │  │ (Port 8001)  │  │  Service     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Core Features

### 1. Dashboard View
- **Real-time System Status**
  - Overall system health indicator
  - Number of active devices
  - Recent alerts count
  - System uptime

- **Key Metrics Visualization**
  - Current consumption trends
  - Vibration levels
  - Temperature monitoring
  - Quick status cards for critical parameters

### 2. Device Monitoring
- **Device List**
  - All connected devices
  - Status indicators (online/offline/warning/critical)
  - Filter by tenant (multi-tenant support)
  - Search functionality

- **Device Detail View**
  - Real-time sensor data
    - Motor current
    - Vibration (X, Y, Z axes)
    - Temperature
  - Historical data charts (last 1h, 6h, 24h, 7d)
  - Safety status indicators
  - AI analysis results
    - Anomaly detection
    - Wear prediction
    - Optimization recommendations

### 3. Alert Management
- **Alert List**
  - Chronological alert feed
  - Priority levels (critical, warning, info)
  - Filter by device, type, date
  - Mark as read/acknowledged

- **Alert Details**
  - Full alert context
  - Device information
  - Sensor readings at alert time
  - Recommended actions
  - Alert history

### 4. Notification System
- **Push Notifications**
  - Critical alerts (immediate)
  - Warning alerts (batched)
  - Customizable notification preferences
  - Quiet hours support

- **In-App Notifications**
  - Notification badge
  - Notification center
  - Sound and vibration alerts

### 5. User Profile & Settings
- **Authentication**
  - API key management
  - Biometric authentication (Face ID, Touch ID, Fingerprint)
  - Session management

- **Preferences**
  - Update frequency (realtime, 30s, 1m, 5m)
  - Notification settings
  - Preferred units (metric/imperial)
  - Theme (light/dark mode)
  - Language selection

- **Tenant Selection**
  - Switch between tenants (multi-tenant users)
  - View tenant-specific devices

### 6. Offline Support
- **Local Data Cache**
  - Last known device states
  - Recent sensor data
  - Alert history
  - Automatic sync when online

- **Offline Indicators**
  - Clear offline status banner
  - Last update timestamp
  - Auto-reconnect with exponential backoff

## API Integration

### Authentication
```typescript
// API Key Authentication
headers: {
  'X-API-Key': 'user_api_key',
  'X-Tenant-ID': 'tenant_id' // Optional for multi-tenant
}
```

### REST Endpoints

#### Device Operations
```typescript
// Get all devices
GET /devices
Response: Device[]

// Get device data
GET /devices/{id}/data
Response: SensorData

// Get device safety status
GET /devices/{id}/safety
Response: SafetyStatus

// Get AI analysis
GET /devices/{id}/ai-analysis
Response: AIAnalysis
```

#### Alert Operations
```typescript
// Get alerts
GET /alerts?device_id={id}&severity={level}&since={timestamp}
Response: Alert[]

// Acknowledge alert
POST /alerts/{id}/acknowledge
Body: { acknowledged_by: string, notes: string }
```

#### User Operations
```typescript
// Get user profile
GET /user/profile
Response: UserProfile

// Update notification preferences
PUT /user/preferences
Body: NotificationPreferences
```

### WebSocket Integration
```typescript
// Connect to real-time updates
ws://control-api:8000/ws/device/{device_id}

// Message types
{
  type: "sensor_data" | "alert" | "safety_status",
  device_id: string,
  timestamp: number,
  data: any
}
```

## Security Considerations

### Data Protection
- **Encryption**
  - TLS 1.3 for all network communication
  - End-to-end encryption for sensitive data
  - Secure storage for API keys and tokens

- **Authentication**
  - API key validation
  - Token refresh mechanism
  - Biometric authentication support
  - Session timeout (configurable)

### Network Security
- **Certificate Pinning**
  - Prevent man-in-the-middle attacks
  - Pin specific certificates or public keys

- **Request Validation**
  - Input sanitization
  - Rate limiting on client side
  - Timeout configuration

### Privacy
- **Data Minimization**
  - Only cache necessary data
  - Clear cache on logout
  - Respect data retention policies

- **Permissions**
  - Request only required permissions
  - Explain permission usage
  - Graceful degradation without optional permissions

## Push Notification Service

### Architecture
```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   Mobile    │◄─────►│ Push Service │◄─────►│   FCM/APNs  │
│    App      │       │   (Backend)  │       │  (Cloud)    │
└─────────────┘       └──────────────┘       └─────────────┘
                             ▲
                             │
                      ┌──────▼──────┐
                      │  Control    │
                      │   Layer     │
                      └─────────────┘
```

### Push Service Implementation
```python
# python-control-layer/push_service.py
from typing import List, Dict
import asyncio
from firebase_admin import messaging, credentials, initialize_app

class PushNotificationService:
    """Send push notifications for critical events"""
    
    def __init__(self, config: Dict):
        self.fcm_enabled = config.get('fcm_enabled', False)
        self.apns_enabled = config.get('apns_enabled', False)
        
        if self.fcm_enabled:
            cred = credentials.Certificate(config['fcm_credentials'])
            initialize_app(cred)
    
    async def send_alert(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Dict,
        priority: str = "high"
    ):
        """Send push notification to mobile devices"""
        if not self.fcm_enabled:
            return
        
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data,
            tokens=device_tokens,
            android=messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound='default',
                    color='#FF0000' if priority == 'high' else '#FFA500'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1
                    )
                )
            )
        )
        
        response = messaging.send_multicast(message)
        return response
```

### Notification Categories
```typescript
enum NotificationPriority {
  CRITICAL = 'critical',  // Immediate delivery
  WARNING = 'warning',    // Batched delivery (5 min)
  INFO = 'info'           // Batched delivery (15 min)
}

interface AlertNotification {
  title: string;          // "Critical Alert: ESP32_001"
  body: string;           // "Motor current exceeded threshold"
  priority: NotificationPriority;
  data: {
    device_id: string;
    alert_type: string;
    severity: string;
    timestamp: number;
    action_url: string;   // Deep link to device detail
  };
}
```

## User Experience Design

### Design Principles
1. **Safety First**
   - No control operations from mobile
   - Clear read-only indicators
   - Prominent safety status

2. **Clarity**
   - Clear status indicators
   - Consistent color coding (green/yellow/red)
   - Simple, scannable information

3. **Efficiency**
   - Quick access to critical information
   - Minimal taps to key features
   - Smart defaults and caching

4. **Responsiveness**
   - Real-time updates where critical
   - Smooth animations and transitions
   - Optimistic UI updates

### Color Scheme
- **Success/Normal:** Green (#4CAF50)
- **Warning:** Yellow/Orange (#FFA726)
- **Critical/Error:** Red (#F44336)
- **Info:** Blue (#2196F3)
- **Offline:** Gray (#9E9E9E)

### Icon System
- Use Material Icons (Android) / SF Symbols (iOS)
- Consistent icon usage across platforms
- Clear status badge system

## Development Roadmap

### Phase 1: MVP (Months 1-2)
- [ ] Basic authentication (API key)
- [ ] Device list and detail view
- [ ] Real-time data display
- [ ] Alert list and notifications
- [ ] Offline support basics

### Phase 2: Enhanced Features (Months 3-4)
- [ ] Multi-tenant support
- [ ] Advanced filtering and search
- [ ] Historical data charts
- [ ] Push notifications
- [ ] Biometric authentication

### Phase 3: Polish & Optimization (Months 5-6)
- [ ] Performance optimization
- [ ] Advanced offline capabilities
- [ ] Widget support (home screen widgets)
- [ ] Apple Watch / Wear OS companion
- [ ] Localization (i18n)

## Testing Strategy

### Unit Tests
- Component testing
- State management logic
- API client functions
- Utility functions

### Integration Tests
- API integration
- WebSocket connectivity
- Push notification handling
- Offline sync logic

### E2E Tests
- User flows (login, view device, acknowledge alert)
- Cross-platform compatibility
- Network conditions (slow, offline, unstable)

### Device Testing
- iOS: iPhone 12+, iPad
- Android: Multiple manufacturers (Samsung, Google, Xiaomi)
- Various screen sizes and resolutions

## Deployment

### iOS Deployment
- **Requirements:**
  - Apple Developer Account ($99/year)
  - Xcode 14+
  - macOS for building

- **Distribution:**
  - TestFlight for beta testing
  - App Store for production

### Android Deployment
- **Requirements:**
  - Google Play Developer Account ($25 one-time)
  - Android Studio

- **Distribution:**
  - Internal testing track
  - Closed beta track
  - Production release on Google Play

### CI/CD Pipeline
```yaml
# .github/workflows/mobile-app.yml
name: Mobile App CI/CD

on:
  push:
    paths:
      - 'mobile-app/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm install
      - name: Run tests
        run: npm test
      - name: Lint
        run: npm run lint

  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build iOS
        run: |
          cd mobile-app
          npx react-native build-ios

  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Android
        run: |
          cd mobile-app
          npx react-native build-android
```

## Monitoring & Analytics

### Application Performance
- **Crash Reporting:** Firebase Crashlytics / Sentry
- **Performance Monitoring:** Firebase Performance
- **Analytics:** Firebase Analytics / Mixpanel

### Key Metrics
- Daily/Monthly Active Users
- Session duration
- Screen views and navigation paths
- API response times
- Crash-free rate
- Push notification opt-in rate
- Alert acknowledgment time

## Future Enhancements

### Advanced Features
- **AR Guidance:** Augmented reality for maintenance procedures
- **Voice Commands:** Voice-activated monitoring
- **Smart Widgets:** Home screen widgets for quick status
- **Wearable Integration:** Apple Watch and Wear OS support
- **Offline Analytics:** Local AI analysis when offline
- **Collaborative Features:** Team chat and handoff

### Integration Opportunities
- **Calendar Integration:** Scheduled maintenance reminders
- **Contact Integration:** Quick call to maintenance team
- **Map Integration:** Location-based device discovery
- **Share Features:** Export and share reports

## References

- [React Native Documentation](https://reactnative.dev/)
- [Flutter Documentation](https://flutter.dev/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [Apple Push Notification Service](https://developer.apple.com/documentation/usernotifications)
- [Material Design Guidelines](https://material.io/design)
- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)

## Related Documentation

- [API Documentation](API.md)
- [Authentication Guide](AUTHENTICATION_IMPLEMENTATION_GUIDE.md)
- [Security](SECURITY.md)
- [Multi-Tenant Architecture](MULTI_TENANT_ARCHITECTURE.md)
