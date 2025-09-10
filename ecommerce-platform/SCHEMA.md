# Database Schema Design for E-commerce Platform 🗄️

## Table of Contents
1. [Database Design Strategy](#database-design-strategy)
2. [Entity Relationship Model](#entity-relationship-model)
3. [Complete Schema Definition](#complete-schema-definition)
4. [Indexing Strategy](#indexing-strategy)
5. [Performance Optimizations](#performance-optimizations)
6. [Data Consistency & Constraints](#data-consistency--constraints)
7. [Scalability Considerations](#scalability-considerations)
8. [Migration Strategy](#migration-strategy)
9. [Best Practices](#best-practices)

## Database Design Strategy

### Design Principles

When designing a database schema for an e-commerce platform, you need to consider:

1. **Domain-Driven Design**: Tables directly map to your business entities
2. **Normalization**: Eliminate data redundancy while maintaining performance
3. **Performance**: Optimize for common query patterns
4. **Scalability**: Design for growth (10M users, 1000 orders/sec)
5. **Data Integrity**: Enforce business rules at the database level
6. **Flexibility**: Allow for future feature additions

### From Domain Model to Database Tables

Your existing entities translate beautifully to database tables:

```
Domain Entity → Database Table → Key Considerations
User         → users          → Polymorphic design for Customer/Seller/Admin
Product      → products       → Rich metadata, search optimization
Cart         → carts & cart_items → Session management, persistence
Order        → orders & order_items → Immutable snapshots, state tracking
Payment      → payments & refunds → Financial data integrity
Inventory    → inventory_items → Concurrency control, real-time updates
```

### Database Choice: PostgreSQL

**Why PostgreSQL?**
- **ACID Compliance**: Critical for financial transactions
- **JSON Support**: Flexible for product attributes and addresses
- **Full-Text Search**: Built-in search capabilities for products
- **Concurrent Performance**: Handles high transaction volumes
- **Rich Data Types**: Arrays, UUIDs, custom types
- **Mature Ecosystem**: Excellent tooling and extensions

## Entity Relationship Model

### Core Relationships

```
Users (1) ←→ (M) Orders
Users (1) ←→ (M) Carts  
Users (1) ←→ (M) Payments
Sellers (1) ←→ (M) Products
Products (1) ←→ (M) Cart_Items
Products (1) ←→ (M) Order_Items
Products (1) ←→ (M) Inventory_Items
Orders (1) ←→ (M) Order_Items
Orders (1) ←→ (1) Payments
Warehouses (1) ←→ (M) Inventory_Items
```

### Inheritance Patterns

**User Hierarchy**: Using Single Table Inheritance with discriminator
- Base: `users` table with `user_type` column
- Extensions: `customer_profiles`, `seller_profiles`, `admin_profiles`

## Complete Schema Definition

### 1. Users & Authentication

```sql
-- Core users table (single table inheritance)
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('CUSTOMER', 'SELLER', 'ADMIN')),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for performance
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Customer-specific data
CREATE TABLE customer_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    shipping_addresses JSONB DEFAULT '[]'::jsonb,
    billing_addresses JSONB DEFAULT '[]'::jsonb,
    date_of_birth DATE,
    loyalty_points INTEGER DEFAULT 0,
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seller-specific data
CREATE TABLE seller_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    business_type VARCHAR(50),
    tax_id VARCHAR(50),
    business_address JSONB,
    bank_details JSONB, -- Encrypted sensitive data
    commission_rate DECIMAL(5,4) DEFAULT 0.05, -- 5% default
    is_verified BOOLEAN DEFAULT false,
    verification_documents JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Admin-specific data (minimal for now)
CREATE TABLE admin_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'ADMIN',
    permissions JSONB DEFAULT '[]'::jsonb,
    department VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Authentication tokens
CREATE TABLE user_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_type VARCHAR(20) NOT NULL CHECK (token_type IN ('ACCESS', 'REFRESH', 'RESET_PASSWORD', 'EMAIL_VERIFICATION')),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_tokens_user_id (user_id),
    INDEX idx_user_tokens_type_expires (token_type, expires_at)
);
```

### 2. Product Catalog

```sql
-- Product categories (hierarchical)
CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    parent_category_id UUID REFERENCES categories(category_id),
    description TEXT,
    image_url VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', name || ' ' || COALESCE(description, ''))) STORED
);

-- Products table
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES users(user_id),
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    
    -- Pricing (in cents to avoid floating point issues)
    price_amount BIGINT NOT NULL CHECK (price_amount > 0), -- Store as cents
    price_currency VARCHAR(3) DEFAULT 'USD',
    compare_at_price_amount BIGINT, -- Original price for discounts
    cost_price_amount BIGINT, -- Seller's cost (for profit calculations)
    
    -- Product metadata
    sku VARCHAR(100) UNIQUE,
    barcode VARCHAR(100),
    weight_grams INTEGER,
    dimensions JSONB, -- {length: 10, width: 5, height: 2, unit: "cm"}
    
    -- Category and attributes
    category_id UUID REFERENCES categories(category_id),
    attributes JSONB DEFAULT '{}'::jsonb, -- Flexible product attributes
    variants JSONB DEFAULT '[]'::jsonb, -- Size, color, etc.
    
    -- SEO and marketing
    meta_title VARCHAR(255),
    meta_description TEXT,
    tags TEXT[], -- PostgreSQL array for tags
    
    -- Product status
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED')),
    is_digital BOOLEAN DEFAULT false,
    requires_shipping BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Full-text search vector
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', name), 'A') ||
        setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(tags, ' '), '')), 'C')
    ) STORED
);

-- Product images
CREATE TABLE product_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product reviews and ratings
CREATE TABLE product_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    customer_id UUID NOT NULL REFERENCES users(user_id),
    order_id UUID, -- Link to order for verified purchases
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(255),
    content TEXT,
    is_verified_purchase BOOLEAN DEFAULT false,
    is_approved BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate reviews from same customer
    UNIQUE(product_id, customer_id)
);
```

### 3. Shopping Cart

```sql
-- Shopping carts
CREATE TABLE carts (
    cart_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- For guest carts
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ABANDONED', 'CONVERTED')),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Cart metadata
    notes TEXT,
    discount_codes JSONB DEFAULT '[]'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    
    -- Either customer_id or session_id must be provided
    CHECK (customer_id IS NOT NULL OR session_id IS NOT NULL)
);

-- Cart items
CREATE TABLE cart_items (
    cart_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL REFERENCES carts(cart_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    
    -- Price snapshot (at time of adding to cart)
    unit_price_amount BIGINT NOT NULL,
    unit_price_currency VARCHAR(3) NOT NULL,
    
    -- Product variant selection
    variant_options JSONB DEFAULT '{}'::jsonb, -- {size: "L", color: "red"}
    
    -- Timestamps
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicate items
    UNIQUE(cart_id, product_id, variant_options)
);
```

### 4. Order Management

```sql
-- Orders table
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL, -- Human-readable order number
    customer_id UUID NOT NULL REFERENCES users(user_id),
    
    -- Order status
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'CONFIRMED', 'PAID', 'PROCESSING', 'SHIPPED', 
        'DELIVERED', 'CANCELLED', 'REFUNDED', 'RETURNED'
    )),
    
    -- Financial information (all amounts in cents)
    subtotal_amount BIGINT NOT NULL,
    tax_amount BIGINT DEFAULT 0,
    shipping_amount BIGINT DEFAULT 0,
    discount_amount BIGINT DEFAULT 0,
    total_amount BIGINT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Addresses (stored as JSONB for flexibility)
    shipping_address JSONB NOT NULL,
    billing_address JSONB NOT NULL,
    
    -- Order metadata
    notes TEXT,
    special_instructions TEXT,
    gift_message TEXT,
    tracking_number VARCHAR(100),
    
    -- Timestamps for order lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Estimated delivery
    estimated_delivery_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Order items (immutable snapshot)
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id),
    
    -- Product snapshot (immutable at time of order)
    product_name VARCHAR(500) NOT NULL,
    product_sku VARCHAR(100),
    product_image_url VARCHAR(500),
    
    -- Pricing snapshot
    unit_price_amount BIGINT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    total_price_amount BIGINT NOT NULL,
    
    -- Product variant selected
    variant_options JSONB DEFAULT '{}'::jsonb,
    
    -- Fulfillment
    fulfillment_status VARCHAR(20) DEFAULT 'PENDING' CHECK (fulfillment_status IN (
        'PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED'
    )),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order status history (audit trail)
CREATE TABLE order_status_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    changed_by UUID REFERENCES users(user_id), -- Who made the change
    reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Payment Processing

```sql
-- Payments table
CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id),
    customer_id UUID NOT NULL REFERENCES users(user_id),
    
    -- Payment details
    amount_charged BIGINT NOT NULL, -- Amount in cents
    currency VARCHAR(3) NOT NULL,
    
    -- Payment method
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN (
        'CREDIT_CARD', 'DEBIT_CARD', 'UPI', 'WALLET', 'NET_BANKING', 'COD'
    )),
    
    -- Payment status
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', 'REFUNDED', 'PARTIALLY_REFUNDED'
    )),
    
    -- Payment provider data
    provider VARCHAR(50), -- STRIPE, RAZORPAY, PAYPAL, etc.
    provider_transaction_id VARCHAR(255),
    provider_response JSONB, -- Store full provider response
    
    -- Payment metadata
    gateway_fee_amount BIGINT DEFAULT 0,
    net_amount BIGINT, -- Amount after gateway fees
    
    -- Card information (tokenized/masked)
    card_last_four VARCHAR(4),
    card_brand VARCHAR(20),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    
    -- Risk and fraud
    risk_score DECIMAL(3,2), -- 0.00 to 1.00
    fraud_check_result JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    error_code VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Refunds table
CREATE TABLE refunds (
    refund_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(payment_id),
    order_id UUID NOT NULL REFERENCES orders(order_id),
    
    -- Refund details
    refund_amount BIGINT NOT NULL, -- Amount in cents
    currency VARCHAR(3) NOT NULL,
    reason VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Refund status
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED'
    )),
    
    -- Provider details
    provider_refund_id VARCHAR(255),
    provider_response JSONB,
    
    -- Processing
    processed_by UUID REFERENCES users(user_id), -- Admin who processed
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    error_code VARCHAR(50),
    error_message TEXT
);
```

### 6. Inventory Management

```sql
-- Warehouses
CREATE TABLE warehouses (
    warehouse_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL, -- Unique warehouse code
    
    -- Location
    address JSONB NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Warehouse details
    type VARCHAR(20) DEFAULT 'FULFILLMENT' CHECK (type IN ('FULFILLMENT', 'DROPSHIP', 'RETAIL')),
    max_capacity INTEGER,
    current_utilization DECIMAL(5,2) DEFAULT 0.00, -- Percentage
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    operating_hours JSONB, -- {monday: {open: "09:00", close: "18:00"}, ...}
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Inventory items (product stock in warehouses)
CREATE TABLE inventory_items (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(warehouse_id),
    
    -- Stock levels
    available_quantity INTEGER NOT NULL DEFAULT 0 CHECK (available_quantity >= 0),
    reserved_quantity INTEGER NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    committed_quantity INTEGER NOT NULL DEFAULT 0 CHECK (committed_quantity >= 0),
    damaged_quantity INTEGER NOT NULL DEFAULT 0 CHECK (damaged_quantity >= 0),
    
    -- Stock tracking
    total_received INTEGER DEFAULT 0,
    total_sold INTEGER DEFAULT 0,
    total_adjusted INTEGER DEFAULT 0,
    
    -- Reorder settings
    reorder_point INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    max_stock_level INTEGER,
    
    -- Location in warehouse
    location_bin VARCHAR(20),
    location_shelf VARCHAR(20),
    
    -- Timestamps
    last_stock_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_count_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(product_id, warehouse_id),
    
    -- Constraint: available + reserved + committed + damaged = total on hand
    CHECK (available_quantity + reserved_quantity + committed_quantity + damaged_quantity >= 0)
);

-- Inventory reservations (for checkout process)
CREATE TABLE inventory_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES users(user_id),
    order_id UUID REFERENCES orders(order_id), -- Linked when order is placed
    
    -- Reservation details
    items JSONB NOT NULL, -- [{"product_id": "...", "quantity": 2, "warehouse_id": "..."}]
    
    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN (
        'ACTIVE', 'CONFIRMED', 'CANCELLED', 'EXPIRED'
    )),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '15 minutes'),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE
);

-- Inventory movements (audit trail for all stock changes)
CREATE TABLE inventory_movements (
    movement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory_items(inventory_id),
    
    -- Movement details
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN (
        'INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'TRANSFER', 'DAMAGE', 'RETURN'
    )),
    quantity_change INTEGER NOT NULL, -- Positive for inbound, negative for outbound
    reference_type VARCHAR(20), -- ORDER, PURCHASE, ADJUSTMENT, etc.
    reference_id UUID, -- ID of the related record
    
    -- Before/after quantities
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    
    -- Metadata
    reason VARCHAR(100),
    notes TEXT,
    unit_cost_amount BIGINT, -- Cost per unit in cents
    
    -- Who made the change
    changed_by UUID REFERENCES users(user_id),
    
    -- Timestamps
    movement_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 7. Notifications System

```sql
-- Notification templates
CREATE TABLE notification_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN (
        'ORDER_CONFIRMATION', 'ORDER_SHIPPED', 'ORDER_DELIVERED', 'ORDER_CANCELLED',
        'PAYMENT_SUCCESS', 'PAYMENT_FAILED', 'REFUND_PROCESSED',
        'LOW_STOCK_ALERT', 'WELCOME', 'PASSWORD_RESET', 'EMAIL_VERIFICATION'
    )),
    
    -- Channel-specific templates
    email_subject VARCHAR(255),
    email_body_html TEXT,
    email_body_text TEXT,
    sms_content VARCHAR(160),
    push_title VARCHAR(100),
    push_body VARCHAR(255),
    
    -- Template variables
    variables JSONB DEFAULT '[]'::jsonb, -- ["customer_name", "order_number", etc.]
    
    -- Settings
    is_active BOOLEAN DEFAULT true,
    language VARCHAR(5) DEFAULT 'en',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Notification preferences (per user)
CREATE TABLE notification_preferences (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    
    -- Channel preferences
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    
    -- Timing preferences
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Frequency settings
    frequency VARCHAR(20) DEFAULT 'IMMEDIATE' CHECK (frequency IN ('IMMEDIATE', 'DAILY', 'WEEKLY', 'DISABLED')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (user_id, notification_type)
);

-- Notifications queue/log
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    template_id UUID REFERENCES notification_templates(template_id),
    
    -- Notification details
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('EMAIL', 'SMS', 'PUSH', 'IN_APP')),
    
    -- Content
    subject VARCHAR(255),
    content TEXT NOT NULL,
    recipient VARCHAR(255) NOT NULL, -- Email address, phone number, etc.
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'QUEUED' CHECK (status IN (
        'QUEUED', 'SENDING', 'SENT', 'DELIVERED', 'FAILED', 'BOUNCED'
    )),
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    
    -- Priority
    priority VARCHAR(10) DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 8. Analytics & Reporting Tables

```sql
-- Order analytics (denormalized for performance)
CREATE TABLE order_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(order_id),
    
    -- Date dimensions
    order_date DATE NOT NULL,
    order_year INTEGER NOT NULL,
    order_month INTEGER NOT NULL,
    order_day INTEGER NOT NULL,
    order_weekday INTEGER NOT NULL, -- 1-7
    
    -- Customer dimensions
    customer_id UUID NOT NULL,
    customer_type VARCHAR(20), -- NEW, RETURNING
    customer_segment VARCHAR(50),
    
    -- Product dimensions
    product_categories TEXT[], -- All categories in the order
    product_count INTEGER NOT NULL,
    
    -- Financial metrics (in cents)
    subtotal_amount BIGINT NOT NULL,
    tax_amount BIGINT NOT NULL,
    shipping_amount BIGINT NOT NULL,
    discount_amount BIGINT NOT NULL,
    total_amount BIGINT NOT NULL,
    
    -- Fulfillment metrics
    fulfillment_time_hours INTEGER, -- Time from order to shipment
    delivery_time_hours INTEGER, -- Time from shipment to delivery
    
    -- Geography
    shipping_country VARCHAR(2),
    shipping_state VARCHAR(100),
    shipping_city VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product performance analytics
CREATE TABLE product_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    
    -- Date dimension
    date DATE NOT NULL,
    
    -- Sales metrics
    units_sold INTEGER DEFAULT 0,
    revenue_amount BIGINT DEFAULT 0, -- In cents
    views INTEGER DEFAULT 0,
    cart_additions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4) DEFAULT 0.0000,
    
    -- Inventory metrics
    stock_level INTEGER DEFAULT 0,
    stock_turns DECIMAL(10,4) DEFAULT 0.0000,
    
    -- Rating metrics
    average_rating DECIMAL(3,2) DEFAULT 0.00,
    review_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(product_id, date)
);
```

## Indexing Strategy

### Primary Indexes for Performance

```sql
-- User-related indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_type_active ON users(user_type, is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Product search and filtering
CREATE INDEX idx_products_seller ON products(seller_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_price ON products(price_amount);
CREATE INDEX idx_products_created_at ON products(created_at);
CREATE INDEX idx_products_search ON products USING GIN(search_vector);
CREATE INDEX idx_products_tags ON products USING GIN(tags);

-- Cart performance
CREATE INDEX idx_carts_customer ON carts(customer_id);
CREATE INDEX idx_carts_session ON carts(session_id);
CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX idx_cart_items_product ON cart_items(product_id);

-- Order queries
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Payment processing
CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_customer ON payments(customer_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider_txn ON payments(provider_transaction_id);
CREATE INDEX idx_refunds_payment ON refunds(payment_id);

-- Inventory management
CREATE INDEX idx_inventory_product_warehouse ON inventory_items(product_id, warehouse_id);
CREATE INDEX idx_inventory_warehouse ON inventory_items(warehouse_id);
CREATE INDEX idx_inventory_low_stock ON inventory_items(available_quantity) WHERE available_quantity <= reorder_point;
CREATE INDEX idx_inventory_movements_inventory ON inventory_movements(inventory_id);
CREATE INDEX idx_inventory_movements_date ON inventory_movements(movement_date);

-- Notifications
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at);

-- Analytics (time-series queries)
CREATE INDEX idx_order_analytics_date ON order_analytics(order_date);
CREATE INDEX idx_order_analytics_customer ON order_analytics(customer_id);
CREATE INDEX idx_product_analytics_date ON product_analytics(date);
CREATE INDEX idx_product_analytics_product ON product_analytics(product_id);
```

### Composite Indexes for Complex Queries

```sql
-- Common product search patterns
CREATE INDEX idx_products_category_status_price ON products(category_id, status, price_amount);
CREATE INDEX idx_products_seller_status ON products(seller_id, status);

-- Order dashboard queries
CREATE INDEX idx_orders_customer_status_date ON orders(customer_id, status, created_at);
CREATE INDEX idx_orders_status_date ON orders(status, created_at);

-- Inventory alerts
CREATE INDEX idx_inventory_warehouse_low_stock ON inventory_items(warehouse_id, available_quantity) 
WHERE available_quantity <= reorder_point;

-- Payment reconciliation
CREATE INDEX idx_payments_provider_status_date ON payments(provider, status, created_at);
```

## Performance Optimizations

### 1. Partitioning Strategy

```sql
-- Partition large tables by date for better performance
-- Orders partitioning (by month)
CREATE TABLE orders_y2024m01 PARTITION OF orders
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_y2024m02 PARTITION OF orders
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Similar partitioning for analytics tables
-- order_analytics, notifications, inventory_movements
```

### 2. Materialized Views for Analytics

```sql
-- Product performance summary
CREATE MATERIALIZED VIEW product_performance_summary AS
SELECT 
    p.product_id,
    p.name,
    p.price_amount,
    p.seller_id,
    COALESCE(SUM(oi.quantity), 0) as total_sold,
    COALESCE(SUM(oi.total_price_amount), 0) as total_revenue,
    COALESCE(AVG(pr.rating), 0) as avg_rating,
    COUNT(pr.review_id) as review_count,
    COALESCE(SUM(ii.available_quantity), 0) as total_stock
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN product_reviews pr ON p.product_id = pr.product_id AND pr.is_approved = true
LEFT JOIN inventory_items ii ON p.product_id = ii.product_id
WHERE p.status = 'ACTIVE'
GROUP BY p.product_id, p.name, p.price_amount, p.seller_id;

-- Refresh strategy
CREATE INDEX ON product_performance_summary(product_id);
-- Refresh hourly: REFRESH MATERIALIZED VIEW CONCURRENTLY product_performance_summary;
```

### 3. Database Functions for Business Logic

```sql
-- Function to calculate product availability across warehouses
CREATE OR REPLACE FUNCTION get_product_availability(p_product_id UUID)
RETURNS TABLE(total_available INTEGER, warehouses JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(ii.available_quantity), 0)::INTEGER as total_available,
        COALESCE(jsonb_agg(
            jsonb_build_object(
                'warehouse_id', w.warehouse_id,
                'warehouse_name', w.name,
                'available_quantity', ii.available_quantity
            )
        ), '[]'::jsonb) as warehouses
    FROM inventory_items ii
    JOIN warehouses w ON ii.warehouse_id = w.warehouse_id
    WHERE ii.product_id = p_product_id 
    AND w.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Function to reserve inventory (atomic operation)
CREATE OR REPLACE FUNCTION reserve_inventory(
    p_customer_id UUID,
    p_items JSONB -- [{"product_id": "...", "quantity": 2}]
) RETURNS UUID AS $$
DECLARE
    v_reservation_id UUID;
    v_item JSONB;
    v_product_id UUID;
    v_quantity INTEGER;
    v_available INTEGER;
BEGIN
    -- Create reservation record
    INSERT INTO inventory_reservations (customer_id, items)
    VALUES (p_customer_id, p_items)
    RETURNING reservation_id INTO v_reservation_id;
    
    -- Reserve inventory for each item
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_product_id := (v_item->>'product_id')::UUID;
        v_quantity := (v_item->>'quantity')::INTEGER;
        
        -- Check and update inventory atomically
        UPDATE inventory_items 
        SET 
            available_quantity = available_quantity - v_quantity,
            reserved_quantity = reserved_quantity + v_quantity
        WHERE product_id = v_product_id
        AND available_quantity >= v_quantity
        RETURNING available_quantity INTO v_available;
        
        -- If no rows updated, insufficient inventory
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Insufficient inventory for product %', v_product_id;
        END IF;
    END LOOP;
    
    RETURN v_reservation_id;
END;
$$ LANGUAGE plpgsql;
```

## Data Consistency & Constraints

### 1. Referential Integrity

```sql
-- Ensure order totals are calculated correctly
CREATE OR REPLACE FUNCTION validate_order_total()
RETURNS TRIGGER AS $$
DECLARE
    calculated_total BIGINT;
BEGIN
    -- Calculate total from order items
    SELECT COALESCE(SUM(total_price_amount), 0)
    INTO calculated_total
    FROM order_items
    WHERE order_id = NEW.order_id;
    
    -- Add tax and shipping, subtract discounts
    calculated_total := calculated_total + NEW.tax_amount + NEW.shipping_amount - NEW.discount_amount;
    
    -- Validate total matches
    IF calculated_total != NEW.total_amount THEN
        RAISE EXCEPTION 'Order total mismatch. Expected: %, Got: %', calculated_total, NEW.total_amount;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_order_total
    BEFORE INSERT OR UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION validate_order_total();
```

### 2. Data Integrity Checks

```sql
-- Ensure inventory quantities are never negative
ALTER TABLE inventory_items 
ADD CONSTRAINT check_inventory_non_negative 
CHECK (available_quantity >= 0 AND reserved_quantity >= 0);

-- Ensure order item quantities are positive
ALTER TABLE order_items 
ADD CONSTRAINT check_order_item_quantity_positive 
CHECK (quantity > 0 AND total_price_amount >= 0);

-- Ensure payment amounts are positive
ALTER TABLE payments 
ADD CONSTRAINT check_payment_amount_positive 
CHECK (amount_charged > 0);

-- Ensure user emails are unique and valid
CREATE UNIQUE INDEX idx_users_email_unique ON users(LOWER(email));
```

## Scalability Considerations

### 1. Horizontal Scaling Strategies

#### Read Replicas
```sql
-- Configure read replicas for read-heavy workloads
-- Master: Handles all writes (orders, payments, inventory updates)
-- Replicas: Handle reads (product catalog, order history, analytics)
```

#### Sharding Strategy
```sql
-- Potential sharding strategies:
-- 1. Customer-based sharding (by customer_id hash)
-- 2. Geographic sharding (by shipping region)
-- 3. Seller-based sharding (by seller_id for catalog)

-- Example: Customer-based sharding function
CREATE OR REPLACE FUNCTION get_shard_id(customer_id UUID)
RETURNS INTEGER AS $$
BEGIN
    -- Simple hash-based sharding (4 shards)
    RETURN (hashtext(customer_id::text) % 4) + 1;
END;
$$ LANGUAGE plpgsql;
```

### 2. Caching Strategy

```sql
-- Identify cacheable data:
-- 1. Product catalog (cache for 1 hour)
-- 2. Category hierarchy (cache for 24 hours)
-- 3. User sessions (cache for 30 minutes)
-- 4. Cart contents (cache for 15 minutes)
-- 5. Inventory levels (cache for 5 minutes)

-- Redis cache keys pattern:
-- product:{product_id} -> Product details
-- category:hierarchy -> Category tree
-- cart:{customer_id} -> Cart contents
-- inventory:{product_id} -> Stock levels
```

### 3. Archive Strategy

```sql
-- Archive old data to keep main tables performant
CREATE TABLE orders_archive (LIKE orders INCLUDING ALL);
CREATE TABLE order_items_archive (LIKE order_items INCLUDING ALL);

-- Archive orders older than 2 years
CREATE OR REPLACE FUNCTION archive_old_orders()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move old orders to archive
    WITH moved_orders AS (
        DELETE FROM orders 
        WHERE created_at < CURRENT_DATE - INTERVAL '2 years'
        AND status IN ('DELIVERED', 'CANCELLED', 'REFUNDED')
        RETURNING *
    )
    INSERT INTO orders_archive SELECT * FROM moved_orders;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;
```

## Migration Strategy

### 1. Schema Versioning

```sql
-- Migration tracking table
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    checksum VARCHAR(64)
);

-- Example migration script structure
-- V001__create_users_table.sql
-- V002__add_user_preferences.sql
-- V003__create_products_table.sql
```

### 2. Zero-Downtime Migrations

```sql
-- Safe migration patterns:
-- 1. Additive changes (new columns, indexes)
-- 2. Backward compatible changes
-- 3. Feature flags for new functionality

-- Example: Adding new column safely
-- Step 1: Add nullable column
ALTER TABLE products ADD COLUMN meta_description TEXT;

-- Step 2: Populate with default values (batched)
UPDATE products SET meta_description = LEFT(description, 160) 
WHERE meta_description IS NULL AND id BETWEEN 1 AND 10000;

-- Step 3: Add NOT NULL constraint (after data populated)
ALTER TABLE products ALTER COLUMN meta_description SET NOT NULL;
```

## Best Practices

### 1. Data Modeling Best Practices

1. **Use UUIDs for Primary Keys**: Better for distributed systems and prevents enumeration attacks
2. **Store Money as Integers**: Avoid floating-point precision issues (store cents)
3. **Use JSONB for Flexible Data**: Product attributes, addresses, metadata
4. **Implement Soft Deletes**: Use `deleted_at` timestamps instead of hard deletes
5. **Version Critical Data**: Keep audit trails for orders, payments, inventory
6. **Normalize vs Denormalize**: Normalize for consistency, denormalize for performance

### 2. Security Best Practices

```sql
-- Row-level security for multi-tenant data
CREATE POLICY customer_orders_policy ON orders
FOR ALL TO application_user
USING (customer_id = current_setting('app.current_user_id')::UUID);

-- Encrypt sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypt bank details
INSERT INTO seller_profiles (user_id, bank_details)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    pgp_sym_encrypt('{"account": "1234567890"}', 'encryption_key')
);
```

### 3. Performance Best Practices

1. **Index Strategy**: Create indexes for all foreign keys and frequent query patterns
2. **Query Optimization**: Use EXPLAIN ANALYZE to optimize slow queries
3. **Connection Pooling**: Use PgBouncer or similar for connection management
4. **Monitoring**: Track query performance and slow query logs
5. **Maintenance**: Regular VACUUM, ANALYZE, and REINDEX operations

### 4. Backup and Recovery

```sql
-- Backup strategy
-- 1. Daily full backups
-- 2. Continuous WAL archiving
-- 3. Point-in-time recovery capability
-- 4. Cross-region backup replication

-- Example backup command
-- pg_dump --format=custom --no-owner --no-privileges ecommerce_db > backup_$(date +%Y%m%d).dump
```

## Conclusion

This database schema design provides:

✅ **Scalable Foundation**: Designed for 10M+ users and high transaction volumes  
✅ **Data Integrity**: Strong constraints and referential integrity  
✅ **Performance Optimized**: Proper indexing and query optimization  
✅ **Business Logic Support**: Functions and triggers for complex operations  
✅ **Audit Trail**: Complete tracking of data changes  
✅ **Flexible Design**: JSONB for extensible attributes  
✅ **Security Focused**: Encryption and access controls  

### Key Takeaways

1. **Start with Domain Model**: Your entities directly inform table design
2. **Plan for Scale**: Consider partitioning, sharding, and archiving early
3. **Index Strategically**: Index for your query patterns, not all columns
4. **Maintain Data Integrity**: Use constraints and triggers for business rules
5. **Monitor Performance**: Regular analysis and optimization
6. **Version Everything**: Track schema changes and data migrations

Your e-commerce platform now has a robust, scalable database foundation that can grow with your business! 🚀
