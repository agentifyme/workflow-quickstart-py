from agentifyme import task, workflow
from loguru import logger
from pydantic import BaseModel


# Data Models
class CoffeeOrder(BaseModel):
    order_id: str
    customer_id: str
    drink_type: str
    size: str
    extras: list[str] = []


class OrderPrice(BaseModel):
    order_id: str
    base_price: float
    extras_cost: float
    loyalty_discount: float
    final_total: float


class InventoryItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    low_stock_threshold: int


class InventoryUpdate(BaseModel):
    items_used: list[tuple[str, int]]
    restock_needed: list[str]


class LoyaltyPoints(BaseModel):
    customer_id: str
    points_earned: int
    total_points: int
    current_tier: str


class OrderSummary(BaseModel):
    order_id: str
    price_info: OrderPrice
    loyalty_info: LoyaltyPoints
    inventory_status: str
    status: str
    estimated_wait: int


# Tasks - All synchronous now
@task(name="Calculate Order Price")
def calculate_order_price(order: CoffeeOrder, loyalty_tier: str) -> OrderPrice:
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
    initial_loyalty = calculate_loyalty_points(0, order.customer_id)
    price_info = calculate_order_price(order, initial_loyalty.current_tier)
    final_loyalty = calculate_loyalty_points(price_info.final_total, order.customer_id)
    return price_info, final_loyalty


@workflow(name="Process Inventory")
def process_inventory(order: CoffeeOrder) -> InventoryUpdate:
    inventory_update = check_inventory(order)
    if inventory_update.restock_needed:
        logger.warning(f"Low stock alert for items: {inventory_update.restock_needed}")
    return inventory_update


@workflow(name="Process Order")
def process_order(order: CoffeeOrder) -> OrderSummary:
    try:
        # Process pricing
        price_info, loyalty_info = process_pricing(order)

        # Process inventory
        inventory_update = process_inventory(order)

        inventory_status = "READY_TO_PREPARE" if not inventory_update.restock_needed else "WARNING_LOW_STOCK"

        base_wait = 5
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
