import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
import re
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal



#defining the fields to be returned
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

class CreateCustomer(graphene.Mutation):
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if phone:
            if not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
                raise Exception("Invalid phone format")

        try:
            customer = Customer.objects.create(
                name=name,
                email=email,
                phone=phone
            )
        except IntegrityError:
            raise Exception("Email already exists")

        return CreateCustomer(
            customer=customer,
            message="Customer created successfully"
        )

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCreateCustomers(graphene.Mutation):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    def mutate(self, info, input):
        created = []
        errors = []

        for idx, data in enumerate(input):
            try:
                with transaction.atomic():
                    customer = Customer.objects.create(
                        name=data.name,
                        email=data.email,
                        phone=data.phone
                    )
                    created.append(customer)
            except IntegrityError:
                errors.append(f"Record {idx}: Email already exists")
            except Exception as e:
                errors.append(f"Record {idx}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product.objects.create(
            name=name,
            price=price,
            stock=stock
        )
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)

    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        if not product_ids:
            raise Exception("At least one product is required")

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            raise Exception("One or more product IDs are invalid")

        total = sum([p.price for p in products], Decimal("0.00"))

        order = Order.objects.create(
            customer=customer,
            total_amount=total,
            order_date=order_date or timezone.now()
        )
        order.products.set(products)

        return CreateOrder(order=order)

import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)

    def resolve_all_customers(self, info):
        return Customer.objects.all()
