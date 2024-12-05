from agentifyme import task, workflow
from loguru import logger
from pydantic import BaseModel, Field


# Data Models
class CoffeeOrder(BaseModel):
    """
    Represents a coffee order placed by a customer.
    """

    order_id: str = Field(description="Unique identifier for the order.")
    customer_id: str = Field(description="Unique identifier for the customer placing the order.")
    drink_type: str = Field(description="Type of drink ordered (e.g., latte, cappuccino).")
    size: str = Field(description="Size of the drink (e.g., small, medium, large).")
    extras: list[str] = Field(description="List of additional items requested for the drink.", default=[])


class OrderPrice(BaseModel):
    """
    Represents the price information for a coffee order.
    """

    order_id: str = Field(description="Unique identifier for the order.")
    base_price: float = Field(description="Base price of the drink.")
    extras_cost: float = Field(description="Cost of additional items requested for the drink.")
    loyalty_discount: float = Field(description="Discount applied due to loyalty tier.")
    final_total: float = Field(description="Final total price after applying discounts.")


class InventoryItem(BaseModel):
    """
    Represents an item in the inventory.
    """

    item_id: str = Field(description="Unique identifier for the item.")
    name: str = Field(description="Name of the item.")
    quantity: int = Field(description="Current quantity of the item in stock.")
    low_stock_threshold: int = Field(description="Threshold quantity below which low stock alert is triggered.")


class InventoryUpdate(BaseModel):
    """
    Represents the update to the inventory after processing an order.
    """

    items_used: list[tuple[str, int]] = Field(description="List of items used in the order and their quantities.")
    restock_needed: list[str] = Field(description="List of items that need to be restocked.")


class LoyaltyPoints(BaseModel):
    """
    Represents the loyalty points information for a customer.
    """

    customer_id: str = Field(description="Unique identifier for the customer.")
    points_earned: int = Field(description="Points earned by the customer for the order.")
    total_points: int = Field(description="Total points accumulated by the customer.")
    current_tier: str = Field(description="Current loyalty tier of the customer.")


class OrderSummary(BaseModel):
    """
    Represents the summary of a coffee order.
    """

    order_id: str = Field(description="Unique identifier for the order.")
    price_info: OrderPrice = Field(description="Price information for the order.")
    loyalty_info: LoyaltyPoints = Field(description="Loyalty points information for the order.")
    inventory_status: str = Field(description="Status of the inventory after processing the order.")
    status: str = Field(description="Status of the order after processing.")
    estimated_wait: int = Field(description="Estimated wait time for the order to be prepared.")


# Tasks - All synchronous now
@task(name="Calculate Order Price")
def calculate_order_price(order: CoffeeOrder, loyalty_tier: str) -> OrderPrice:
    """
    Calculates the price of a coffee order based on the order details and loyalty tier.

    Args:
        order (CoffeeOrder): The coffee order details.
        loyalty_tier (str): The loyalty tier of the customer.

    Returns:
        OrderPrice: The price information for the order.
    """

    base_prices = {"small": 3.50, "medium": 4.00, "large": 4.50}
    drink_markups = {"latte": 1.00, "cappuccino": 1.00, "espresso": 0.50}
    extra_prices = {"extra_shot": 0.80, "whipped_cream": 0.50, "syrup": 0.50}

    base_price = base_prices[order.size] + drink_markups.get(order.drink_type, 0)
    extras_cost = sum(extra_prices.get(extra, 0) for extra in order.extras)

    discount_rates = {"bronze": 0.0, "silver": 0.05, "gold": 0.10}
    loyalty_discount = (base_price + extras_cost) * discount_rates.get(loyalty_tier, 0)

    return OrderPrice(
        order_id=order.order_id,
        base_price=base_price,
        extras_cost=extras_cost,
        loyalty_discount=loyalty_discount,
        final_total=base_price + extras_cost - loyalty_discount,
    )


@task(name="Check Inventory")
def check_inventory(order: CoffeeOrder) -> InventoryUpdate:
    """
    Checks the inventory for the items required to prepare a coffee order.

    Args:
        order (CoffeeOrder): The coffee order details.

    Returns:
        InventoryUpdate: The update to the inventory after processing the order.
    """

    # Simulate inventory check
    items_used = [
        ("coffee_beans", 20),
        (
            "milk",
            200 if order.drink_type in ["latte", "cappuccino"] else 0,
        ),
    ]

    if "extra_shot" in order.extras:
        items_used.append(("coffee_beans", 10))

    restock_needed = ["coffee_beans"] if order.drink_type == "espresso" else []

    return InventoryUpdate(items_used=items_used, restock_needed=restock_needed)


@task(name="Calculate Loyalty")
def calculate_loyalty_points(order_price: float, customer_id: str) -> LoyaltyPoints:
    """
    Calculates the loyalty points earned by a customer based on the order price.

    Args:
        order_price (float): The total price of the order.
        customer_id (str): The unique identifier for the customer.

    Returns:
        LoyaltyPoints: The loyalty points information for the order.
    """

    points_earned = int(order_price)
    mock_current_points = 100
    total_points = mock_current_points + points_earned

    tier = "bronze"
    if total_points > 500:
        tier = "gold"
    elif total_points > 200:
        tier = "silver"

    return LoyaltyPoints(
        customer_id=customer_id,
        points_earned=points_earned,
        total_points=total_points,
        current_tier=tier,
    )


# Workflows
@workflow(name="Process Pricing")
def process_pricing(order: CoffeeOrder) -> tuple[OrderPrice, LoyaltyPoints]:
    """
    Processes the pricing for a coffee order.

    Args:
        order (CoffeeOrder): The coffee order details.

    Returns:
        tuple[OrderPrice, LoyaltyPoints]: The price information and loyalty points information for the order.
    """

    initial_loyalty = calculate_loyalty_points(0, order.customer_id)
    price_info = calculate_order_price(order, initial_loyalty.current_tier)
    final_loyalty = calculate_loyalty_points(price_info.final_total, order.customer_id)
    return price_info, final_loyalty


@workflow(name="Process Inventory")
def process_inventory(order: CoffeeOrder) -> InventoryUpdate:
    """
    Processes the inventory for a coffee order.

    Args:
        order (CoffeeOrder): The coffee order details.

    Returns:
        InventoryUpdate: The update to the inventory after processing the order.
    """

    inventory_update = check_inventory(order)
    if inventory_update.restock_needed:
        logger.warning(f"Low stock alert for items: {inventory_update.restock_needed}")
    return inventory_update


@workflow(name="Process Order")
def process_order(order: CoffeeOrder) -> OrderSummary:
    """
    Processes the entire order workflow.

    Args:
        order (CoffeeOrder): The coffee order details.

    Returns:
        OrderSummary: The summary of the order after processing.
    """

    try:
        # Process pricing
        price_info, loyalty_info = process_pricing(order)

        # Process inventory
        inventory_update = process_inventory(order)

        inventory_status = "READY_TO_PREPARE" if not inventory_update.restock_needed else "WARNING_LOW_STOCK"

        base_wait = 5
        logger.info(f"{order} , {type(order)}")
        extra_wait = len(order.extras) * 1

        return OrderSummary(
            order_id=order.order_id,
            price_info=price_info,
            loyalty_info=loyalty_info,
            inventory_status=inventory_status,
            status="ACCEPTED",
            estimated_wait=base_wait + extra_wait,
        )

    except Exception as e:
        logger.error(f"Error processing order {order.order_id}: {str(e)}")
        raise


def main():
    # Create a sample order
    order = CoffeeOrder(
        order_id="CO123",
        customer_id="CUST456",
        drink_type="latte",
        size="medium",
        extras=["extra_shot", "whipped_cream"],
    )

    # Process the order
    result = process_order(order)

    print("\nOrder Summary:")
    print(f"Order ID: {result.order_id}")
    print(f"Final Price: ${result.price_info.final_total:.2f}")
    print(f"Loyalty Points: {result.loyalty_info.points_earned}")
    print(f"Wait Time: {result.estimated_wait} minutes")
    print(f"Status: {result.inventory_status}")


if __name__ == "__main__":
    main()
