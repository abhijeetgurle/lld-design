#!/usr/bin/env python3
"""
Script to generate ER diagram for the e-commerce platform LLD design
"""

import os
from mermaid import Mermaid

def create_er_diagram():
    """Create and save the ER diagram as PNG"""
    
    mermaid_code = """
erDiagram
    User ||--o{ Order : "places"
    User ||--o{ Cart : "owns"
    User ||--o{ Payment : "makes"
    User ||--o{ NotificationPreference : "has"
    User ||--o{ Notification : "receives"
    
    Customer ||--|| User : "is-a"
    Seller ||--|| User : "is-a"
    Admin ||--|| User : "is-a"
    
    Product }o--|| Seller : "created_by"
    Product ||--o{ CartItem : "contains"
    Product ||--o{ OrderItem : "contains"
    Product ||--o{ InventoryItem : "tracked_in"
    
    Cart ||--o{ CartItem : "contains"
    Cart ||--|| Order : "converts_to"
    
    Order ||--o{ OrderItem : "contains"
    Order ||--o| Payment : "has"
    Order ||--o{ Notification : "triggers"
    
    Payment ||--o| Refund : "can_have"
    
    InventoryItem }o--|| Warehouse : "stored_in"
    InventoryItem ||--o{ InventoryReservation : "reserved_by"
    
    NotificationTemplate ||--o{ Notification : "generates"
    
    User {
        string user_id PK
        string email
        string name
        datetime created_at
        boolean is_active
        string user_type "Customer/Seller/Admin"
    }
    
    Customer {
        string user_id PK,FK
        string[] shipping_addresses
    }
    
    Seller {
        string user_id PK,FK
        string business_name
    }
    
    Admin {
        string user_id PK,FK
    }
    
    Product {
        string product_id PK
        string name
        string description
        Money price
        string category
        string seller_id FK
        datetime created_at
    }
    
    Cart {
        string cart_id PK
        string customer_id FK
        datetime created_at
    }
    
    CartItem {
        string product_id PK,FK
        string cart_id FK
        int quantity
        Money unit_price
    }
    
    Order {
        string order_id PK
        string customer_id FK
        OrderStatus status
        Money total_amount
        datetime created_at
        datetime confirmed_at
        datetime shipped_at
        datetime delivered_at
    }
    
    OrderItem {
        string order_id FK
        string product_id FK
        string product_name
        int quantity
        Money unit_price
    }
    
    Payment {
        string payment_id PK
        string order_id FK
        string customer_id FK
        Money amount
        PaymentMethod method
        PaymentStatus status
        datetime created_at
        datetime processed_at
        string transaction_id
        string error_message
    }
    
    Refund {
        string refund_id PK
        string original_payment_id FK
        Money amount
        string reason
        PaymentStatus status
        datetime created_at
        datetime processed_at
    }
    
    InventoryItem {
        string product_id PK,FK
        string warehouse_id PK,FK
        int available_quantity
        int reserved_quantity
        int total_received
        int total_sold
        datetime last_updated
    }
    
    InventoryReservation {
        string reservation_id PK
        string customer_id FK
        ReservationStatus status
        datetime created_at
        datetime expires_at
        datetime confirmed_at
        datetime cancelled_at
    }
    
    Warehouse {
        string warehouse_id PK
        string name
        string location
        boolean is_active
        int max_capacity
        datetime created_at
    }
    
    Notification {
        string notification_id PK
        string user_id FK
        NotificationType notification_type
        NotificationChannel channel
        string subject
        string body
        NotificationStatus status
        Priority priority
        datetime created_at
        datetime sent_at
        datetime delivered_at
        int retry_count
        string recipient
        string error_message
    }
    
    NotificationTemplate {
        string template_id PK
        NotificationType notification_type
        NotificationChannel channel
        string subject_template
        string body_template
        string language
        boolean is_active
        datetime created_at
    }
    
    NotificationPreference {
        string user_id PK,FK
        NotificationType notification_type PK
        NotificationChannel[] enabled_channels
        boolean is_enabled
        string quiet_hours_start
        string quiet_hours_end
        string timezone
    }
    
    Money {
        float amount
        string currency
    }
"""
    
    try:
        # Create Mermaid instance
        mermaid = Mermaid()
        
        # Generate PNG
        output_path = "ecommerce_platform_er_diagram.png"
        
        print(f"Generating ER diagram...")
        mermaid.to_png(mermaid_code, output_path)
        
        print(f"✅ ER diagram successfully generated: {output_path}")
        print(f"📁 Full path: {os.path.abspath(output_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating diagram: {str(e)}")
        return False

if __name__ == "__main__":
    create_er_diagram()
