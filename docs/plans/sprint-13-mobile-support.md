# Sprint 13: iOS & Android Mobile Analytics Support

**Status:** Planned  
**Duration:** 2 weeks  
**Goal:** Extend MCP-Metrics to support iOS and Android app analytics via GA4 mobile data streams and Firebase SDK integration.

---

## Overview

Extend the platform from web-only to support **mobile apps** (iOS and Android). GA4 natively supports multiple data stream types per property — this sprint adds the ability to create and manage iOS and Android data streams alongside existing web streams.

### What You'll Be Able To Do

```bash
# Create iOS app analytics
analytics-mcp create \
  --name "My iOS App" \
  --platform ios \
  --bundle-id com.example.myapp \
  --blueprint mobile-saas

# Create Android app analytics  
analytics-mcp create \
  --name "My Android App" \
  --platform android \
  --package-name com.example.myapp \
  --blueprint mobile-ecommerce

# List all platforms for a product
analytics-mcp status --property-id 123456789
# → Shows: Web stream (G-XXXX), iOS stream, Android stream
```

---

## Technical Scope

### 1. Data Model Changes

**File:** `backend/src/models/site.py`

```python
# Add platform_type to Site model
platform_type: Mapped[str] = mapped_column(String(20), default="web")  # web|ios|android
bundle_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # iOS
package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Android
app_store_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # iOS App Store
firebase_app_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

**Migration:** Alembic migration to add columns (nullable for backward compatibility).

---

### 2. GA4 Service Extensions

**File:** `backend/src/services/ga4_service.py`

Add mobile-specific methods:

```python
def create_ios_data_stream(
    self, 
    property_id: str, 
    bundle_id: str,
    app_store_id: str | None = None,
    site: Site | None = None,
    actor: str = "system",
    actor_type: str = "system",
) -> dict[str, Any]:
    """Create iOS app data stream for GA4 property."""

def create_android_data_stream(
    self,
    property_id: str,
    package_name: str,
    site: Site | None = None,
    actor: str = "system", 
    actor_type: str = "system",
) -> dict[str, Any]:
    """Create Android app data stream for GA4 property."""

def provision_for_app(
    self,
    site: Site,
    actor: str = "system",
    actor_type: str = "system",
) -> dict[str, Any]:
    """Full provisioning for mobile app (property + data stream)."""
```

---

### 3. Google API Client Updates

**File:** `backend/src/services/google_clients_real.py`

Implement mobile stream creation:

```python
def create_ios_data_stream(
    self, 
    property_id: str, 
    bundle_id: str,
    app_store_id: str | None = None,
) -> dict[str, Any]:
    """Create iOS data stream via GA4 Admin API."""
    from google.analytics.admin_v1alpha.types import DataStream
    
    stream = DataStream(
        type_="IOS_APP_DATA_STREAM",
        display_name=f"iOS App: {bundle_id}",
        ios_app_stream_data={
            "bundle_id": bundle_id,
            "app_store_id": app_store_id or "",
        },
    )
    # ... create via client

def create_android_data_stream(
    self,
    property_id: str,
    package_name: str,
) -> dict[str, Any]:
    """Create Android data stream via GA4 Admin API."""
    from google.analytics.admin_v1alpha.types import DataStream
    
    stream = DataStream(
        type_="ANDROID_APP_DATA_STREAM",
        display_name=f"Android App: {package_name}",
        android_app_stream_data={
            "package_name": package_name,
        },
    )
    # ... create via client
```

---

### 4. Mobile Blueprints

**New Files:**
- `docs/blueprints/mobile-saas.yaml`
- `docs/blueprints/mobile-ecommerce.yaml`
- `docs/blueprints/mobile-content.yaml`

**Mobile-Specific Events:**

```yaml
name: mobile-saas
description: SaaS mobile app tracking blueprint
version: "1.0"
platform: mobile  # ios|android|both
events:
  - name: screen_view
    description: App screen viewed (replaces page_view)
    parameters: [screen_name, screen_class]
    
  - name: app_open
    description: App launched or brought to foreground
    parameters: [source, campaign, medium]
    
  - name: signup_started
    description: User began registration flow
    parameters: [method, source]
    
  - name: signup_completed
    description: User completed registration
    parameters: [method, plan_name]
    
  - name: subscription_started
    description: User initiated purchase/subscription
    parameters: [product_id, price, currency]
    
  - name: subscription_completed
    description: Successful purchase/subscription
    parameters: [product_id, price, currency, transaction_id]
    
  - name: feature_used
    description: Key feature engagement
    parameters: [feature_name, feature_category]

user_properties:
  - name: subscription_tier
    description: free|basic|pro|enterprise
  - name: user_since
    description: First app open timestamp
  - name: last_active
    description: Last app open timestamp

sdk_config:
  ios:
    pod: 'Firebase/Analytics'
    min_version: '10.0.0'
    import: 'FirebaseAnalytics'
  android:
    gradle: 'com.google.firebase:firebase-analytics:21.5.0'
    import: 'com.google.firebase.analytics.FirebaseAnalytics'
```

---

### 5. SDK Snippet Generation

**File:** `backend/src/services/snippet_service.py` (new)

Generate platform-specific integration code:

**iOS (Swift):**
```swift
// AppDelegate.swift or @main App struct
import FirebaseCore
import FirebaseAnalytics

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil
    ) -> Bool {
        FirebaseApp.configure()
        return true
    }
}

// Tracking events
Analytics.logEvent("signup_started", parameters: [
    AnalyticsParameterMethod: method,
    "source": source
])

Analytics.logEvent("signup_completed", parameters: [
    AnalyticsParameterMethod: method,
    "plan_name": planName
])

Analytics.logEvent("screen_view", parameters: [
    AnalyticsParameterScreenName: screenName,
    AnalyticsParameterScreenClass: screenClass
])
```

**Android (Kotlin):**
```kotlin
// Application class or MainActivity
import com.google.firebase.analytics.FirebaseAnalytics
import com.google.firebase.analytics.logEvent

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        FirebaseApp.initializeApp(this)
    }
}

// Activity tracking
val firebaseAnalytics = Firebase.analytics

// Track events
firebaseAnalytics.logEvent("signup_started") {
    param(FirebaseAnalytics.Param.METHOD, method)
    param("source", source)
}

firebaseAnalytics.logEvent("signup_completed") {
    param(FirebaseAnalytics.Param.METHOD, method)
    param("plan_name", planName)
}

firebaseAnalytics.logEvent(FirebaseAnalytics.Event.SCREEN_VIEW) {
    param(FirebaseAnalytics.Param.SCREEN_NAME, screenName)
    param(FirebaseAnalytics.Param.SCREEN_CLASS, screenClass)
}
```

---

### 6. CLI & API Updates

**CLI:** `cli/analytics_cli.py`

Add platform flags:

```python
@app.command()
def create(
    name: str = typer.Option(..., "--name", "-n", help="Site/app name"),
    domain: str | None = typer.Option(None, "--domain", "-d", help="Domain (for web)"),
    platform: str = typer.Option("web", "--platform", "-p", help="Platform: web|ios|android"),
    bundle_id: str | None = typer.Option(None, "--bundle-id", help="iOS bundle ID (e.g., com.example.app)"),
    package_name: str | None = typer.Option(None, "--package-name", help="Android package name"),
    app_store_id: str | None = typer.Option(None, "--app-store-id", help="iOS App Store ID"),
    blueprint: str = typer.Option("saas", "--blueprint", "-b", help="Blueprint name"),
):
    """Create analytics setup for web or mobile app."""
    # Validate platform-specific args
    if platform == "ios" and not bundle_id:
        raise typer.BadParameter("--bundle-id required for iOS apps")
    if platform == "android" and not package_name:
        raise typer.BadParameter("--package-name required for Android apps")
    # ... create logic
```

**API:** `backend/src/api/routes/sites.py`

Update `CreateSiteRequest`:

```python
class CreateSiteRequest(BaseModel):
    name: str
    domain: str | None = Field(None, description="Required for web, optional for mobile")
    platform_type: str = Field("web", pattern="^(web|ios|android)$")
    bundle_id: str | None = Field(None, description="iOS bundle ID")
    package_name: str | None = Field(None, description="Android package name")
    app_store_id: str | None = Field(None, description="iOS App Store ID")
    blueprint: str = "saas"
    environment: str = "prod"
```

---

### 7. MCP Tool Updates

**File:** `backend/src/mcp/server.py`

Add mobile-specific tools:

```python
class CreateMobileAppRequest(BaseModel):
    name: str = Field(..., description="App name")
    platform: str = Field(..., pattern="^(ios|android)$")
    bundle_id: str | None = Field(None, description="iOS bundle ID")
    package_name: str | None = Field(None, description="Android package name")
    app_store_id: str | None = Field(None, description="iOS App Store ID")
    blueprint: str = Field("mobile-saas", description="Mobile blueprint to apply")

@mcp.tool()
async def create_mobile_app_analytics(request: CreateMobileAppRequest) -> str:
    """Create GA4 property with iOS or Android data stream."""
    # Implementation

@mcp.tool()
async def get_mobile_sdk_snippet(domain: str, platform: str) -> str:
    """Get Firebase Analytics SDK integration code for iOS or Android."""
    # Return platform-specific code
```

---

### 8. Web UI Updates

**New Views:**
- Mobile app creation flow (platform selector, bundle ID/package name inputs)
- SDK snippet display with syntax highlighting (Swift/Kotlin)
- Platform comparison view (Web + iOS + Android streams for same product)

**Components:**
- `PlatformSelector` — tabs for Web/iOS/Android
- `MobileSdkSnippet` — code display with copy button
- `BundleIdInput` — validation for reverse-DNS format
- `PackageNameInput` — validation for Android package naming

---

### 9. Testing

**Unit Tests:**
- `test_ga4_service_mobile.py` — iOS/Android stream creation
- `test_snippet_service.py` — SDK code generation
- `test_mobile_blueprints.py` — mobile blueprint loading

**Integration Tests:**
- End-to-end iOS app provisioning
- End-to-end Android app provisioning
- Multi-platform property (web + mobile)

---

## Acceptance Criteria

- [ ] Can create iOS data stream with bundle ID
- [ ] Can create Android data stream with package name  
- [ ] Mobile blueprints define screen_view, app_open, and app-specific events
- [ ] CLI supports `--platform ios|android` with validation
- [ ] API returns platform-specific SDK snippets (Swift/Kotlin)
- [ ] Web UI has mobile app creation flow
- [ ] MCP tools support mobile analytics creation
- [ ] All 8 existing tests pass + new mobile tests added
- [ ] Documentation updated with mobile setup guide

---

## Risks & Considerations

1. **Firebase Linking** — GA4 mobile streams require Firebase project. May need to auto-create or require pre-existing Firebase setup.

2. **GTM Mobile** — Mobile GTM uses Firebase Remote Config backend. Simpler than web (no DOM), but different deployment model.

3. **App Store Requirements** — iOS App Store ID needed for full attribution. May require user to provide post-App Store submission.

4. **Platform Validation** — Bundle IDs and package names have strict formats. Need validation regexes.

5. **Hybrid Apps** — Cordova, React Native, Flutter use different integration patterns. Consider "hybrid" platform type for Sprint 14.

---

## Post-Sprint Possibilities

- **Sprint 14:** Hybrid app support (React Native, Flutter)
- **Sprint 15:** App store attribution (iOS App Store, Google Play Console linking)
- **Sprint 16:** In-app purchase tracking validation
