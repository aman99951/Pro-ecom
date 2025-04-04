from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username


class BillingAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_1}, {self.city}"


class ShippingAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_1}, {self.city}"


class SiteSetting(models.Model):
    site_title = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_title


class Category(models.Model):
    name = models.CharField(max_length=255)

    def get_absolute_url(self):
        return reverse('category_detail', args=[str(self.id)])

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, related_name='subcategories', on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('Subcategory_detail', args=[str(self.id)])

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        Category, related_name='products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(
        SubCategory, related_name='products', blank=True, null=True, on_delete=models.SET_NULL)
    images = models.ManyToManyField('ProductImage', blank=True)
    featured = models.BooleanField(default=False)
    sale = models.BooleanField(default=False)
    top_selling = models.BooleanField(default=False)
    recommended = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.id)])

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        'Product', related_name='variants', on_delete=models.CASCADE
    )
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    show_size = models.BooleanField(default=True)
    show_color = models.BooleanField(default=True)
    show_price = models.BooleanField(default=True)

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    def apply_discount(self):
        """Apply the active discount to the product variant."""
        discount = self.get_active_discount()
        if discount:
            if discount.discount_type == 'percentage':
                discount_amount = (
                    self.price * discount.discount_value) / Decimal(100)
                self.price -= discount_amount
            elif discount.discount_type == 'fixed':
                self.price -= discount.discount_value
        else:
            self.revert_discount()  # Revert to original price if no active discount

        self.save()

    def revert_discount(self):
        """Revert the price to the original price."""
        if self.original_price:
            self.price = self.original_price
            self.save()

    def get_active_discount(self):
        """Check for any active discount."""
        today = timezone.now().date()
        active_discount = self.discounts.filter(
            start_date__lte=today, end_date__gte=today).first()
        return active_discount

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"


class ProductImage(models.Model):
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image {self.id}"


class ProductLabel(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='labels')
    label = models.CharField(max_length=255)
    value = models.TextField()

    def __str__(self):
        return f"{self.label}: {self.value}"


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='discounts'
    )
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        """Ensure the original price is saved when creating a discount."""
        if self.variant and not self.variant.original_price:
            self.variant.original_price = self.variant.price
            self.variant.save()

        super().save(*args, **kwargs)

        # Apply the discount when saving
        self.variant.apply_discount()

    def __str__(self):
        return f"{self.variant} - {self.discount_type} - {self.discount_value}"


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist"


class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('price', 'Fixed Price'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)

    def is_valid(self):
        now = timezone.now()
        if now < self.valid_from or (self.valid_until and now > self.valid_until):
            return False
        if self.usage_limit is not None and self.usage_limit <= 0:
            return False
        return True

    def apply_discount(self, total_amount):
        if not self.is_valid():
            raise ValidationError("Discount code is not valid.")
        if self.usage_limit is not None:
            self.usage_limit -= 1
            self.save()
        if self.discount_type == 'percentage':
            return total_amount * (1 - self.discount_percentage / 100)
        elif self.discount_type == 'price':
            return max(total_amount - self.discount_price, Decimal('0.00'))
        else:
            raise ValidationError("Invalid discount type.")

    def __str__(self):
        if self.discount_type == 'percentage':
            return f"{self.code} - {self.discount_percentage}%"
        elif self.discount_type == 'price':
            return f"{self.code} - Rs{self.discount_price}"


class DynamicPriceField(models.Model):
    label = models.CharField(
        max_length=100, help_text="Label for the additional charge")
    value = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Value of the additional charge")

    def __str__(self):
        return f"{self.label}: {self.value}"


class Cart(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(
        max_length=40, null=True, blank=True)
    discount_code = models.ForeignKey(
        DiscountCode, on_delete=models.SET_NULL, null=True, blank=True)
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username}'s Cart"
        else:
            return f"Cart with session {self.session_key or 'unknown'}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items',
                             on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_variant} - {self.quantity}"

    def get_total_price(self):
        return Decimal(self.quantity) * Decimal(self.product_variant.price)


class Inventory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='inventory')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    # Adding price to Inventory
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - {self.variant if self.variant else 'Default'}: {self.stock} units"

    def save(self, *args, **kwargs):
        # Save the inventory record
        super(Inventory, self).save(*args, **kwargs)

        # If a variant exists, update its price to match the inventory price
        if self.variant:
            self.variant.price = self.price
            self.variant.save()


class AmazonProduct(models.Model):
    title = models.CharField(max_length=255)
    price = models.CharField(max_length=50)
    image = models.URLField(max_length=500)
    brand = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    url = models.URLField(max_length=500)

    def __str__(self):
        return self.title


class FlipkartProduct(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(blank=True, null=True)
    brand = models.CharField(max_length=255)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    url = models.URLField(max_length=500)

    def __str__(self):
        return self.title


class AjioProduct(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    brand = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    url = models.URLField(max_length=500)

    def __str__(self):
        return self.title


class MyntraProduct(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(max_length=500)
    brand = models.CharField(max_length=100)
    url = models.URLField(max_length=500)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, default=1)
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    billing_address = models.ForeignKey(
        'BillingAddress', on_delete=models.SET_NULL, null=True)
    shipping_address = models.ForeignKey(
        'ShippingAddress', on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(
        max_length=30, default='cash_on_delivery')

    def __str__(self):
        return f"Order {self.id} for {self.user.username}"

    @transaction.atomic
    def checkout(self):
        if not self.cart.items.exists():
            raise ValidationError("Cannot checkout an empty cart.")

        # Set final_price to match cart's final_price
        self.final_price = self.cart.final_price
        self.save()

        for cart_item in self.cart.items.all():
            # Create the OrderItem
            order_item = OrderItem.objects.create(
                order=self,
                product_variant=cart_item.product_variant,
                quantity=cart_item.quantity,
                price=cart_item.get_total_price(),
            )

            # Update inventory stock
            inventory = Inventory.objects.filter(
                variant=cart_item.product_variant).first()
            if inventory and inventory.stock >= cart_item.quantity:
                inventory.stock -= cart_item.quantity
                inventory.save()
            else:
                raise ValidationError(
                    f"Insufficient stock for {cart_item.product_variant.product.name}.")

        # Clear the cart after checkout
        self.cart.items.all().delete()
        self.create_invoice()  # Automatically create the invoice upon checkout
        return self

    def create_invoice(self):
        """
        Creates an invoice for the order if one doesn't already exist.
        """
        if not Invoice.objects.filter(order=self).exists():
            invoice_number = f"INV-{self.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            Invoice.objects.create(
                order=self,
                user=self.user,
                invoice_number=invoice_number,
                amount_due=self.final_price
            )

    def cancel_order(self):
        if self.can_cancel():
            self.status = 'canceled'
            self.save()
            self.cancel_invoices()
        return self

    def cancel_invoices(self):
        """
        Cancels all invoices associated with this order.
        """
        invoices = Invoice.objects.filter(order=self)
        for invoice in invoices:
            invoice.cancel_invoice()

    def can_cancel(self):
        return self.status == 'pending'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, default=1)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product_variant} in Order {self.order.id}"


class Rating(models.Model):
    order = models.ForeignKey(
        Order, related_name='ratings', on_delete=models.CASCADE, default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(
        Product, related_name='ratings', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f'Rating for Order #{self.order.id} - {self.rating} Stars'


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('canceled', 'Canceled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=100, unique=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    issued_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-issued_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f'Invoice {self.invoice_number} for Order {self.order.id}'

    def mark_as_paid(self):
        """
        Marks the invoice as paid and sets the payment date.
        """
        self.status = 'paid'
        self.payment_date = timezone.now()
        self.save()

    def cancel_invoice(self):
        """
        Cancels the invoice.
        """
        self.status = 'canceled'
        self.save()


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    deparment = models.CharField(max_length=20, default='')
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='New')
    attachments = models.FileField(
        upload_to='tickets/attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject
# Model to track agent availability


class TicketAgent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    is_agent = models.BooleanField(default=True)  # Ensure this is an agent

    def __str__(self):
        return f"Agent: {self.user.username}"


class TicketReply(models.Model):
    ticket = models.ForeignKey(
        Ticket, related_name='replies', on_delete=models.CASCADE)
    agent = models.ForeignKey(TicketAgent, null=True, blank=True,
                              on_delete=models.SET_NULL)  # Use TicketAgent for agents
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.ticket.subject}"


class Agent(models.Model):
    username = models.CharField(
        max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128)  # Store hashed password
    name = models.CharField(max_length=20, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_online(self):
        self.is_online = True
        self.save()

    def set_offline(self):
        self.is_online = False
        self.save()

    def save(self, *args, **kwargs):
        # If an Agent is being created or updated, create or update the corresponding User
        if self.username and self.password:
            # Check if a User already exists for this Agent
            user, created = User.objects.get_or_create(username=self.username)

            # If the user was just created, set the password and other details
            if created:
                # Hashes the password and sets it
                user.set_password(self.password)
            else:
                # Update the password if it has changed
                if not check_password(self.password, user.password):
                    user.set_password(self.password)

            # Update other user fields
            user.first_name = self.name or ''  # Optional: set first name
            user.save()

        super().save(*args, **kwargs)  # Call the parent class save method

    def __str__(self):
        return self.username


class ChatRequest(models.Model):
    user = models.ForeignKey(
        User, related_name='chat_requests', on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(
        Agent, related_name='chat_requests', on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=20, null=True, blank=True)
    guest_phone = models.IntegerField(null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    accepted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Chat request from {self.user} to agent {self.agent}"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatRequest, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.message[:50]} to {self.sender}"


class ProblemRequest(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, default=1, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    problem_description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Problem Request from {self.name} ({self.email})"
