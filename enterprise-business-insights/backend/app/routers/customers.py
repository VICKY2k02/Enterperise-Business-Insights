
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Customer, Order, BusinessActivity
from app.schemas.customer import CustomerListItem, PaginatedCustomers, CustomerCreate


router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("", response_model=PaginatedCustomers)
def get_customers(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    status: str | None = Query(default=None, min_length=1, max_length=20),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PaginatedCustomers:

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    try:
        filters = []

        if search:
            term = f"%{search.strip()}%"
            filters.append(
                Customer.name.ilike(term) | Customer.email.ilike(term)
            )

        if status:
            filters.append(Customer.status == status.lower())

        if start_date:
            filters.append(
                Customer.registration_date
                >= datetime.combine(start_date, time.min)
            )

        if end_date:
            filters.append(
                Customer.registration_date
                < datetime.combine(end_date + timedelta(days=1), time.min)
            )

        total = db.scalar(
            select(func.count(Customer.id)).where(*filters)
        ) or 0

        order_count = (
            select(func.count(Order.id))
            .where(Order.customer_id == Customer.id)
            .correlate(Customer)
            .scalar_subquery()
        )

        statement = (
            select(Customer, order_count.label("order_count"))
            .where(*filters)
            .order_by(Customer.registration_date.desc(), Customer.id.desc())
            .offset(offset)
            .limit(limit)
        )

        rows = db.execute(statement).all()

        items = [
            CustomerListItem(
                id=customer.id,
                name=customer.name,
                email=customer.email,
                registration_date=customer.registration_date,
                status=customer.status,
                order_count=orders_count,
            )
            for customer, orders_count in rows
        ]

        return PaginatedCustomers(
            total=total,
            limit=limit,
            offset=offset,
            items=items,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Customers are temporarily unavailable. Please try again.",
        ) from None



@router.post("", response_model=CustomerListItem, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
) -> CustomerListItem:
    try:
        existing_customer = db.scalar(
            select(Customer).where(
                Customer.email == str(customer_data.email)
            )
        )

        if existing_customer:
            raise HTTPException(
                status_code=409,
                detail="A customer with this email already exists.",
            )

        customer = Customer(
            name=customer_data.name.strip(),
            email=str(customer_data.email),
            registration_date=datetime.now(),
            status=customer_data.status.lower(),
        )

        db.add(customer)
        db.flush()

        activity = BusinessActivity(
            activity_type="customer_registered",
            description=f"New customer registered — {customer.name}",
            related_entity="customer",
            related_entity_id=customer.id,
            timestamp=datetime.now(),
        )

        db.add(activity)
        db.commit()
        db.refresh(customer)

        return CustomerListItem(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            registration_date=customer.registration_date,
            status=customer.status,
            order_count=0,
        )

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A customer with this email already exists.",
        ) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Customer registration failed. Please try again.",
        ) from None
