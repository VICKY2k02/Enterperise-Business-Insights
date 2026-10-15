from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    BusinessActivity,
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
)


def seed_database() -> None:
    db = SessionLocal()

    try:
        # -----------------------------
        # Categories
        # -----------------------------
        category_data = [
            {"name": "Electronics", "status": "active"},
            {"name": "Home Appliances", "status": "active"},
            {"name": "Accessories", "status": "active"},
        ]

        categories = {}

        for data in category_data:
            category = db.scalar(
                select(Category).where(
                    Category.name == data["name"]
                )
            )

            if category is None:
                category = Category(**data)
                db.add(category)
                db.flush()

            categories[category.name] = category

        # -----------------------------
        # Products
        # -----------------------------
        product_data = [
            {
                "name": "Laptop Pro 14",
                "category": "Electronics",
                "unit_price": Decimal("85000.00"),
                "unit_cost": Decimal("65000.00"),
            },
            {
                "name": "Smartphone X",
                "category": "Electronics",
                "unit_price": Decimal("45000.00"),
                "unit_cost": Decimal("32000.00"),
            },
            {
                "name": "Air Conditioner",
                "category": "Home Appliances",
                "unit_price": Decimal("55000.00"),
                "unit_cost": Decimal("40000.00"),
            },
            {
                "name": "Wireless Headphones",
                "category": "Accessories",
                "unit_price": Decimal("5000.00"),
                "unit_cost": Decimal("2800.00"),
            },
            {
                "name": "Mechanical Keyboard",
                "category": "Accessories",
                "unit_price": Decimal("4500.00"),
                "unit_cost": Decimal("2500.00"),
            },
        ]

        products = {}

        for data in product_data:
            product = db.scalar(
                select(Product).where(
                    Product.name == data["name"]
                )
            )

            if product is None:
                product = Product(
                    name=data["name"],
                    category_id=categories[data["category"]].id,
                    unit_price=data["unit_price"],
                    unit_cost=data["unit_cost"],
                    status="active",
                )
                db.add(product)
                db.flush()

            products[product.name] = product

        # -----------------------------
        # Customers
        # -----------------------------
        customer_data = [
            {
                "name": "Rahul Sharma",
                "email": "rahul@example.com",
                "registration_date": datetime(2026, 7, 10),
                "status": "active",
            },
            {
                "name": "Priya Reddy",
                "email": "priya@example.com",
                "registration_date": datetime(2026, 7, 18),
                "status": "active",
            },
            {
                "name": "Arjun Kumar",
                "email": "arjun@example.com",
                "registration_date": datetime(2026, 8, 5),
                "status": "active",
            },
            {
                "name": "Sneha Patel",
                "email": "sneha@example.com",
                "registration_date": datetime(2026, 8, 22),
                "status": "active",
            },
            {
                "name": "Vikram Singh",
                "email": "vikram@example.com",
                "registration_date": datetime(2026, 9, 3),
                "status": "active",
            },
        ]

        customers = {}

        for data in customer_data:
            customer = db.scalar(
                select(Customer).where(
                    Customer.email == data["email"]
                )
            )

            if customer is None:
                customer = Customer(**data)
                db.add(customer)
                db.flush()

            customers[customer.email] = customer

        # -----------------------------
        # Orders
        # -----------------------------
        order_data = [
            {
                "reference": "ORD1001",
                "customer": "rahul@example.com",
                "date": datetime(2026, 9, 5, 10, 30),
                "status": "completed",
                "product": "Laptop Pro 14",
                "quantity": 1,
            },
            {
                "reference": "ORD1002",
                "customer": "priya@example.com",
                "date": datetime(2026, 9, 12, 14, 15),
                "status": "completed",
                "product": "Smartphone X",
                "quantity": 2,
            },
            {
                "reference": "ORD1003",
                "customer": "arjun@example.com",
                "date": datetime(2026, 9, 20, 9, 45),
                "status": "completed",
                "product": "Air Conditioner",
                "quantity": 1,
            },
            {
                "reference": "ORD1004",
                "customer": "sneha@example.com",
                "date": datetime(2026, 10, 2, 11, 20),
                "status": "completed",
                "product": "Wireless Headphones",
                "quantity": 3,
            },
            {
                "reference": "ORD1005",
                "customer": "vikram@example.com",
                "date": datetime(2026, 10, 5, 16, 10),
                "status": "completed",
                "product": "Mechanical Keyboard",
                "quantity": 2,
            },
            {
                "reference": "ORD1006",
                "customer": "rahul@example.com",
                "date": datetime(2026, 10, 8, 13, 40),
                "status": "cancelled",
                "product": "Smartphone X",
                "quantity": 1,
            },
            {
                "reference": "ORD1007",
                "customer": "priya@example.com",
                "date": datetime(2026, 10, 10, 15, 30),
                "status": "completed",
                "product": "Laptop Pro 14",
                "quantity": 1,
            },
        ]

        for data in order_data:
            existing_order = db.scalar(
                select(Order).where(
                    Order.id == int(data["reference"].replace("ORD", ""))
                )
            )

            order_id = int(
                data["reference"].replace("ORD", "")
            )

            if existing_order is not None:
                continue

            product = products[data["product"]]

            total_amount = (
                product.unit_price * data["quantity"]
            )

            order = Order(
                id=order_id,
                order_date=data["date"],
                customer_id=customers[data["customer"]].id,
                total_amount=total_amount,
                status=data["status"],
            )

            db.add(order)
            db.flush()

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=data["quantity"],
                unit_price=product.unit_price,
                unit_cost=product.unit_cost,
            )

            db.add(order_item)

        # -----------------------------
        # Business Activities
        # -----------------------------
        activity_data = [
            {
                "activity_type": "order",
                "description": "New order received - ORD1007",
                "related_entity": "order",
                "related_entity_id": 1007,
                "timestamp": datetime(2026, 10, 10, 15, 35),
            },
            {
                "activity_type": "order",
                "description": "Order ORD1005 completed",
                "related_entity": "order",
                "related_entity_id": 1005,
                "timestamp": datetime(2026, 10, 5, 16, 20),
            },
            {
                "activity_type": "customer",
                "description": "New customer registered - Vikram Singh",
                "related_entity": "customer",
                "related_entity_id": customers["vikram@example.com"].id,
                "timestamp": datetime(2026, 9, 3, 10, 0),
            },
        ]

        for data in activity_data:
            existing_activity = db.scalar(
                select(BusinessActivity).where(
                    BusinessActivity.description
                    == data["description"]
                )
            )

            if existing_activity is None:
                db.add(BusinessActivity(**data))

        db.commit()

        print("Database seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()