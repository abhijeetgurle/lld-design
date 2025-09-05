from typing import Optional

from core.entities.cart import Cart


class CartService:
    def __init__(self, cart_repository, product_service) -> None:
        self.cart_repo = cart_repository
        self.product_service = product_service

    def add_item_to_cart(self, customer_id: str, product_id: str, quantity: int) -> Cart:
        # Get or create cart
        cart = self.cart_repo.find_by_customer_id(customer_id)
        if not cart:
            cart = Cart.create_for_customer(customer_id)

        # Validate product exists and is available
        product = self.product_service.get_product(product_id)
        if not product or not product.is_active:
            raise ValueError("Product not available")

        # Add to cart
        cart.add_item(product_id, quantity, product.price)

        # Save cart
        return self.cart_repo.save(cart)

    def remove_item_from_cart(self, customer_id: str, product_id: str) -> Cart:
        """Remove item from cart"""
        cart = self.cart_repo.find_by_customer_id(customer_id)
        if not cart:
            raise ValueError("Cart not found")

        cart.remove_item(product_id)
        return self.cart_repo.save(cart)

    def get_cart_for_customer(self, customer_id: str) -> Optional[Cart]:
        """Get customer's current cart"""
        return self.cart_repo.find_by_customer_id(customer_id)