from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from .models import AjioProduct
from selenium.webdriver.common.by import By
from selenium import webdriver
import json
import re
from decimal import Decimal, InvalidOperation
from django.core.files import File
import os
from urllib.parse import urlsplit
from django.core.files.temp import NamedTemporaryFile
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
import time
import random
from .models import AmazonProduct
from .forms import AmazonProductForm, AjioProductForm
from django.db import IntegrityError, transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging
from django.db import IntegrityError
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib import messages
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from product.forms import RegisterForm, GuestRegisterForm,  CustomPasswordChangeForm, AddressForm, ShippingForm, TicketReplyForm, TicketForm, MyntraProductForm, FlipkartProductForm
from product.decorators import my_login_required, agent_required
from django.contrib.auth.models import User
from product.models import Profile, SiteSetting, Product, Wishlist, Cart, CartItem, ProductVariant, DiscountCode, Inventory, BillingAddress, ShippingAddress, DynamicPriceField, Order, OrderItem, Rating, Invoice, Ticket, TicketReply, Agent, ChatMessage, ProblemRequest, ChatRequest, SubCategory, Category, ProductImage, MyntraProduct, FlipkartProduct
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.views import View
import requests
from bs4 import BeautifulSoup


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
        # Add classes to form fields
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['email'].widget.attrs.update({'class': 'form-control'})
        form.fields['mobile'].widget.attrs.update({'class': 'form-control'})
        form.fields['password1'].widget.attrs.update({'class': 'form-control'})
        form.fields['password2'].widget.attrs.update({'class': 'form-control'})

    return render(request, 'user/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Merge session cart with user's cart before logging in
            merge_carts(request, user)

            # Log the user in
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
        form.fields['username'].label = "Email"  # Rename the label
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget.attrs.update({'class': 'form-control'})

    return render(request, 'user/login.html', {'form': form})


def merge_carts(request, user):
    session_key = request.session.session_key
    if not session_key:
        return  # No session cart to merge

    # Fetch the cart associated with the session key
    session_cart = Cart.objects.filter(
        session_key=session_key, user=None).first()
    if session_cart:
        # Fetch or create the user's cart
        user_cart, created = Cart.objects.get_or_create(user=user)

        # Move items from session cart to user cart
        for item in session_cart.items.all():
            user_cart_item, created = CartItem.objects.get_or_create(
                cart=user_cart, product_variant=item.product_variant
            )
            if not created:
                user_cart_item.quantity += item.quantity
            user_cart_item.total_price = user_cart_item.quantity * \
                user_cart_item.product_variant.price
            user_cart_item.save()

        # Delete the session cart after merging
        session_cart.delete()


@my_login_required
def logout(request):
    auth_logout(request)
    return redirect('login')


def guest_checkout(request):
    if request.method == 'POST':
        register_form = GuestRegisterForm(request.POST)

        if register_form.is_valid():  # Add shipping_form validation
            email = register_form.cleaned_data['email']

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                error_message = "An account with this email already exists."
                return render(request, 'store/guest_checkout.html', {
                    'register_form': register_form,

                    'error_message': error_message,
                })

            # Create the user
            user = register_form.save(commit=False)
            password = get_random_string(length=12)
            user.set_password(password)
            user.username = email
            user.save()

            # Create Profile, Address, and Shipping
            Profile.objects.create(
                user=user, mobile=register_form.cleaned_data['mobile'])

            # Automatically log in the user
            login(request, user)

            # Send email
            try:
                send_mail(
                    'Your Account Details',
                    f'Your account has been created.\n\nUsername: {email}\nPassword: {password}',
                    'your_email@example.com',
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"An error occurred while sending the email: {e}")

            return redirect('home')
        else:
            # Print errors for debugging
            print("Form validation failed.")
            print("Register form errors:", register_form.errors)

    else:
        register_form = GuestRegisterForm()

    context = {
        'register_form': register_form,

    }

    return render(request, 'user/guest_checkout.html', context)


def home(request):
    sale_products = Product.objects.prefetch_related(
        'images', 'variants').filter(sale=True)
    featured_products = Product.objects.prefetch_related(
        'images', 'variants').filter(featured=True)
    top_selling_products = Product.objects.prefetch_related(
        'images', 'variants').filter(top_selling=True)

    context = {
        'sale_products': sale_products,
        'featured_products': featured_products,
        'top_selling_products': top_selling_products
    }

    return render(request, 'home/home.html', context)


def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    if product in wishlist.products.all():
        wishlist.products.remove(product)
    else:
        wishlist.products.add(product)

    return redirect(request.META.get('HTTP_REFERER', 'home', ))


def product_list(request, product_id=None):
    products = Product.objects.all()  # Retrieve all products
    ratings = Rating.objects.filter(
        order__items__product_variant__product__id=product_id
    ).select_related('user')

    # Pagination
    paginator = Paginator(products, 6)  # Show 6 products per page
    page_number = request.GET.get('page')

    try:
        paginated_products = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer, show the first page
        paginated_products = paginator.get_page(1)
    except EmptyPage:
        # If page_number is out of range, show the last page
        paginated_products = paginator.get_page(paginator.num_pages)

    # Combine both dictionaries into a single dictionary
    stars = [1, 2, 3, 4, 5]
    categories = Category.objects.all()
    context = {
        # Pass the paginated products instead of all products
        'products': paginated_products,
        'ratings': ratings,
        'request': request,
        'star': stars,
        "categories": categories,
    }

    return render(request, 'product/product_list.html', context)


def basehome(request):
    # Ensure there is at least one SiteSetting object
    site_settings, created = SiteSetting.objects.get_or_create(
        defaults={'site_title': 'Medicine E-commerce Website'}
    )

    cart_items_count = 0

    # Check for cart based on user or session key
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.items.aggregate(
                total=Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            cart_items_count = 0  # No cart found
    else:
        # Get cart based on session key if user is not authenticated
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
                cart_items_count = cart.items.aggregate(
                    total=Sum('quantity'))['total'] or 0
            except Cart.DoesNotExist:
                cart_items_count = 0  # No cart found for this session

    context = {
        'site_settings': site_settings,
        'cart_items_count': cart_items_count,
    }

    return render(request, 'base.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    variants = product.variants.all()

    # Create a set of unique colors
    unique_colors = {
        variant.color for variant in variants if variant.show_color}

    # Render the template and pass the required context
    return render(request, 'product/product_detail.html', {
        'product': product,
        'variants': variants,
        'unique_colors': unique_colors,  # Pass the unique colors to the template
        'labels': product.labels.all()
    })


@my_login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    context = {
        'wishlist': wishlist
    }
    return render(request, 'product/wishlist.html', context)


@my_login_required
def remove_from_wishlist(request, product_id):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    if product in wishlist.products.all():
        wishlist.products.remove(product)

    return redirect('wishlist_view')


def add_to_cart(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Get or create a cart associated with the logged-in user
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Handle the session cart for anonymous users
        session_key = request.session.session_key or request.session.create()
        cart, created = Cart.objects.get_or_create(
            session_key=session_key, user=None)

    # Check if the item is already in the cart
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product_variant=variant,
    )
    if not item_created:
        cart_item.quantity += 1
    cart_item.save()

    return redirect('view_cart')


def remove_from_cart(request, item_id):
    # Check if user is authenticated
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            return redirect('view_cart')  # or wherever you want to redirect
        cart = get_object_or_404(Cart, session_key=session_key, user=None)

    # Get the cart item to remove
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()  # Remove the item from the cart

    return redirect('view_cart')


def update_cart_item(request, item_id):
    if request.method == "POST":
        quantity = request.POST.get('quantity')
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Update the quantity
        if quantity.isdigit() and int(quantity) > 0:
            cart_item.quantity = int(quantity)
            cart_item.save()
            messages.success(request, "Cart updated successfully.")
        else:
            messages.error(request, "Invalid quantity.")

    return redirect('view_cart')  # Redirect to the cart page


@my_login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        # Initialize instances
        address_instance = BillingAddress.objects.filter(user=user).first()
        shipping_instance = ShippingAddress.objects.filter(user=user).first()

        # Initialize forms
        address_form = AddressForm(
            request.POST if 'save_address' in request.POST else None, instance=address_instance)
        shipping_form = ShippingForm(
            request.POST if 'save_shipping' in request.POST else None, instance=shipping_instance)
        password_form = CustomPasswordChangeForm(
            user=user, data=request.POST if 'change_password' in request.POST else None)

        # Check which form is submitted
        if 'save_address' in request.POST and address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = user
            address.save()
            messages.success(
                request, 'Your billing address has been successfully updated.')
            return redirect('profile')

        if 'save_shipping' in request.POST and shipping_form.is_valid():
            shipping = shipping_form.save(commit=False)
            shipping.user = user
            shipping.save()
            messages.success(
                request, 'Your shipping address has been successfully updated.')
            return redirect('profile')

        if 'change_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Your password has been successfully changed.')
            return redirect('profile')

    else:
        # Initialize forms with current instances
        address_instance = BillingAddress.objects.filter(user=user).first()
        shipping_instance = ShippingAddress.objects.filter(user=user).first()
        address_form = AddressForm(instance=address_instance)
        shipping_form = ShippingForm(instance=shipping_instance)
        password_form = CustomPasswordChangeForm(user=user)

    return render(request, 'user/profile.html', {
        'address_form': address_form,
        'shipping_form': shipping_form,
        'password_form': password_form,
    })


def view_cart(request):
    # Initialize variables
    cart_items = []
    total_price = Decimal('0.00')
    final_price = Decimal('0.00')
    discount_code = None
    discount_code_input = ''
    discount_value = Decimal('0.00')

    wishlist_products = []
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist_products = wishlist.products.all()

    # Handle POST request for wishlist and discount code actions
    if request.method == 'POST':
        # Handle adding/removing items to/from wishlist
        if 'toggle_wishlist' in request.POST:
            product_id = request.POST.get('product_id')
            product = Product.objects.get(id=product_id)
            if product in wishlist_products:
                wishlist.products.remove(product)
                messages.success(
                    request, f"{product.name} removed from your wishlist.")
            else:
                wishlist.products.add(product)
                messages.success(
                    request, f"{product.name} added to your wishlist.")

        # Handle applying/removing discount code
        if 'remove_discount' in request.POST:
            discount_code = None
            request.session.pop('discount_code', None)
            if request.user.is_authenticated:
                cart = Cart.objects.get(user=request.user)
                cart.discount_code = None
                cart.save()
        else:
            discount_code_input = request.POST.get('discount_code', '').strip()
            try:
                discount_code = DiscountCode.objects.get(
                    code=discount_code_input)
                if discount_code.is_valid():
                    request.session['discount_code'] = discount_code_input
                    if request.user.is_authenticated:
                        cart = Cart.objects.get(user=request.user)
                        cart.discount_code = discount_code
                        cart.save()
                    messages.success(
                        request, "Discount code applied successfully!")
                else:
                    messages.error(
                        request, "Discount code is invalid or expired.")
            except DiscountCode.DoesNotExist:
                messages.error(request, "Discount code does not exist.")

    # Retrieve the discount code from the session
    elif 'discount_code' in request.session:
        discount_code_input = request.session['discount_code']
        try:
            discount_code = DiscountCode.objects.get(code=discount_code_input)
            if not discount_code.is_valid():
                messages.error(request, "Discount code is invalid or expired.")
                discount_code = None
                request.session.pop('discount_code', None)
                if request.user.is_authenticated:
                    cart = Cart.objects.get(user=request.user)
                    cart.discount_code = None
                    cart.save()
        except DiscountCode.DoesNotExist:
            discount_code = None
            request.session.pop('discount_code', None)

    # Handle authenticated user cart
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items:
            messages.info(request, "Your cart is currently empty.")

        # Calculate total price and check inventory availability
        for item in cart_items:
            total_price += item.get_total_price()

            # Check inventory availability
            inventory = Inventory.objects.filter(
                variant=item.product_variant).first()
            if inventory and inventory.stock < item.quantity:
                messages.warning(
                    request, f"Only {inventory.stock} of {item.product_variant} available. Quantity updated to available stock.")
                item.quantity = inventory.stock
                item.save()

        # Apply discount if available
        if discount_code:
            discount_value = total_price - \
                discount_code.apply_discount(total_price)
            final_price = total_price - discount_value
        else:
            final_price = total_price

    # Handle guest user cart via session
    else:
        session_key = request.session.session_key or request.session.create()
        cart = Cart.objects.filter(session_key=session_key, user=None).first()

        if cart:
            cart_items = CartItem.objects.filter(cart=cart)
            for item in cart_items:
                total_price += item.get_total_price()
            final_price = total_price
        else:
            messages.info(request, "Your cart is currently empty.")

    # Calculate dynamic price fields and add to final price
    dynamic_price_fields = DynamicPriceField.objects.all()
    dynamic_total = sum(field.value for field in dynamic_price_fields)
    final_price += dynamic_total

    # Save the final price to the cart if authenticated
    if request.user.is_authenticated and cart:
        cart.final_price = final_price
        cart.save()

    # Get recommended products
    recommended_items = Product.objects.filter(recommended=True)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'final_price': final_price,
        'dynamic_price_fields': dynamic_price_fields,
        'discount_value': discount_value,
        'discount_code': discount_code_input if discount_code else '',
        'recommended_items': recommended_items,
        'quantity_options': [1, 2, 3, 4, 5],
        'wishlist_products': wishlist_products,
    }

    return render(request, 'product/cart.html', context)


@my_login_required
def checkout(request):
    # Get the cart for the logged-in user
    cart = get_object_or_404(Cart, user=request.user)

    # Ensure the final price of the cart is already set before proceeding
    if cart.final_price <= 0:
        messages.error(
            request, "Your cart is empty or the final price is not set.")
        return redirect('cart')  # Redirect to cart page

    if request.method == 'POST':
        # Get billing and shipping addresses from the POST data
        billing_address_id = request.POST.get('billing_address')
        shipping_address_id = request.POST.get('shipping_address')

        # Fetch the addresses or return a 404 if not found
        billing_address = get_object_or_404(
            BillingAddress, id=billing_address_id)
        shipping_address = get_object_or_404(
            ShippingAddress, id=shipping_address_id)

        # Always create a new order, even if one for the cart already exists
        order = Order(
            user=request.user,
            cart=cart,
            billing_address=billing_address,
            shipping_address=shipping_address
        )

        try:
            order.checkout()  # Call the checkout method to create the order
            messages.success(
                request, 'Your order has been placed successfully!')
            # Redirect to an order summary page
            return redirect('order_success', order_id=order.id)
        except ValidationError as e:
            messages.error(request, str(e))
        except IntegrityError as e:
            messages.error(
                request, "An error occurred while placing the order. Please try again.")
            return redirect('checkout')

    # Fetch user's billing and shipping addresses
    billing_addresses = BillingAddress.objects.filter(user=request.user)
    shipping_addresses = ShippingAddress.objects.filter(user=request.user)

    return render(request, 'order/checkout.html', {
        'cart': cart,
        'billing_addresses': billing_addresses,
        'shipping_addresses': shipping_addresses,
    })


def order_success(request, order_id):
    # Fetch the order using the order ID
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'order/order_success.html', {
        'order': order,
    })


def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order/order_list.html', {'orders': orders})


logger = logging.getLogger(__name__)


def order_detail(request, order_id):
    logger.info(f'Accessing order detail for order_id: {order_id}')
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Handle the rating submission
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment_value = request.POST.get('comment')

        # Create a new rating instance (assuming you have a Rating model)
        Rating.objects.create(
            order=order,
            user=request.user,
            rating=rating_value,
            comment=comment_value
        )

        messages.success(request, 'Thank you for your feedback!')
        # Redirect to the same order detail page
        return redirect('order_detail', order_id=order.id)
    # This creates a list of ratings from 1 to 5
    rating_range = [1, 2, 3, 4, 5]

    # Pass the list to the context
    context = {
        'order': order,
        'rating_range': rating_range,  # Pass the list for 1 to 5 stars
    }
    return render(request, 'order/order_detail.html', context)


def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.user != request.user:
        messages.error(request, "You are not authorized to cancel this order.")
        return redirect('order_list')

    order.cancel_order()
    messages.success(request, "Your order has been canceled successfully.")
    return redirect('order_list')


def add_billing_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(
                request, 'Your Billing Address is successfully Added.')
            return redirect('profile')  # Redirect to profile after saving
    else:
        form = AddressForm()
    return render(request, 'user/add_address.html', {'form': form})


def add_shipping_address(request):
    if request.method == 'POST':
        form = ShippingForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(
                request, 'Your Shipping Address is successfully Added.')
            return redirect('profile')
    else:
        form = ShippingForm()
    return render(request, 'user/add_address.html', {'form': form})


def reorder(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # Check if the user is authorized to reorder
        if order.user == request.user:
            # Create a new order from the existing order
            new_order = Order.objects.create(
                user=order.user,
                cart=order.cart,  # You may want to create a new cart instead
                final_price=order.final_price,
                billing_address=order.billing_address,
                shipping_address=order.shipping_address,
                status='pending',
                payment_method=order.payment_method,
            )

            # Copy the order items
            for item in order.items.all():
                OrderItem.objects.create(
                    order=new_order,
                    product_variant=item.product_variant,
                    quantity=item.quantity,
                    price=item.price,
                )

            # Create a new invoice for the new order using the `create_invoice` method from the model
            new_order.create_invoice()

            # Redirect to the order list or details page
            return redirect('order_list')

    return redirect('order_detail', order_id=order.id)


@my_login_required
def invoice_list(request):
    user = request.user
    invoices = Invoice.objects.filter(user=user)
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})


@my_login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@my_login_required
def create_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not Invoice.objects.filter(order=order).exists():
        order.create_invoice()  # Use method from Order model
    return redirect('invoice_detail', invoice_id=order.invoice_set.first().id)


@my_login_required
def mark_invoice_as_paid(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    invoice.mark_as_paid()
    return redirect('invoice_detail', invoice_id=invoice.id)


@my_login_required
def cancel_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    invoice.cancel_invoice()
    return redirect('invoice_detail', invoice_id=invoice.id)


@my_login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            return redirect('ticket_list')
    else:
        form = TicketForm()
    return render(request, 'helpdesk/create_ticket.html', {'form': form})


@my_login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(
        user=request.user).prefetch_related('replies')
    return render(request, 'helpdesk/ticket_list.html', {'tickets': tickets})


@my_login_required
def ticket_detail(request, pk):
    # Ensure that the user can only access their own tickets
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)

    # Fetch only the latest reply
    latest_reply = ticket.replies.order_by('-created_at').first()

    if request.method == 'POST':
        if ticket.status != 'Closed':  # Check if the ticket is not closed
            form = TicketReplyForm(request.POST)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.ticket = ticket
                reply.user = request.user  # Associate the reply with the current user
                reply.save()
                return redirect('ticket_detail', pk=ticket.pk)
        else:
            # Handle the case where the ticket is closed
            form = TicketReplyForm()  # Recreate the form to prevent POST submission
            context = {
                'ticket': ticket,
                'latest_reply': latest_reply,
                'form': form,
                'error': 'This ticket is closed and cannot accept new messages.',
            }
            return render(request, 'helpdesk/ticket_detail.html', context)
    else:
        form = TicketReplyForm()

    context = {
        'ticket': ticket,
        'latest_reply': latest_reply,  # Pass only the latest reply
        'form': form,
    }
    return render(request, 'helpdesk/ticket_detail.html', context)


@method_decorator(login_required, name='dispatch')
class TicketChatView(View):
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        replies = TicketReply.objects.filter(
            ticket=ticket).order_by('created_at')
        form = TicketReplyForm()

        context = {
            'ticket': ticket,
            'replies': replies,
            'form': form,
        }
        return render(request, 'admin/ticket_chat.html', context)

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            new_reply = form.save(commit=False)
            new_reply.ticket = ticket
            new_reply.user = request.user  # Ensure user is assigned
            new_reply.save()
            return redirect('ticket-chat', ticket_id=ticket.id)
        else:
            replies = TicketReply.objects.filter(
                ticket=ticket).order_by('created_at')
            context = {
                'ticket': ticket,
                'replies': replies,
                'form': form,
            }
            return render(request, 'admin/ticket_chat.html', context)


@staff_member_required
def sales_report(request):
    products = Product.objects.all()

    # Get search query parameters
    search_query = request.GET.get('q', '')
    category_query = request.GET.get('category', '')
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    # Validate and parse dates
    date_from = parse_datetime(date_from_str) if date_from_str else None
    date_to = parse_datetime(date_to_str) if date_to_str else None

    # Filter products based on search query
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if category_query:
        products = products.filter(category__name=category_query)

    # Filter order items based on date range
    if date_from and date_to:
        order_items = OrderItem.objects.filter(
            order__created_at__range=[date_from, date_to]
        )
    else:
        order_items = OrderItem.objects.all()

    # Aggregate report data
    report_data = []
    for product in products:
        variants = ProductVariant.objects.filter(product=product)
        for variant in variants:
            total_sales = order_items.filter(product_variant=variant).aggregate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('price'))
            )

            report_data.append({
                'product': product.name,
                'variant': variant,
                'total_quantity': total_sales['total_quantity'] or 0,
                'total_revenue': total_sales['total_revenue'] or 0.00,
            })

    context = {
        'report_data': report_data,
        'search_query': search_query,
        'category_query': category_query,
        'date_from': date_from_str,
        'date_to': date_to_str,
    }
    return render(request, 'admin/sales_report.html', context)


# Import transaction for atomicity


def user_chat_request_view(request):
    online_agents = Agent.objects.filter(is_online=True)

    if request.method == 'POST':
        if online_agents.exists():
            agent = online_agents.first()
            user = request.user if request.user.is_authenticated else None

            # Get guest information if the user is not authenticated
            guest_name = request.POST.get('name') if not user else None
            guest_email = request.POST.get('email') if not user else None
            guest_phone = request.POST.get('phone') if not user else None

            if agent:
                try:
                    with transaction.atomic():
                        # Create a chat request
                        chat_request = ChatRequest.objects.create(
                            user=user,
                            guest_name=guest_name,
                            guest_email=guest_email,
                            guest_phone=guest_phone,
                            agent=agent
                        )
                    return redirect('user_chat_session', chat_request_id=chat_request.id)
                except IntegrityError as e:
                    print(f"Error creating chat request: {e}")
                    messages.error(
                        request, "There was an error creating your chat request. Please try again later.")
                    return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})
            else:
                messages.error(
                    request, "No available agent to handle your request.")
                return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})

        else:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            problem_description = request.POST.get('problem_description')

            try:
                ProblemRequest.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    name=name,
                    email=email,
                    phone=phone,
                    problem_description=problem_description
                )
                return render(request, 'chat/thank_you.html')
            except IntegrityError as e:
                print(f"Error creating problem request: {e}")
                messages.error(
                    request, "There was an error submitting your problem. Please try again later.")
                return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})

    return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})


def user_chat_session_view(request, chat_request_id):
    # Fetch the chat request object, no longer filter by user
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id)

    # Process message sending if the form is submitted
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Set sender to the authenticated user or None if not authenticated
            sender = request.user if request.user.is_authenticated else None

            # Create the chat message with the sender as None if user is not authenticated
            ChatMessage.objects.create(
                session=chat_request,
                sender=sender,
                message=message_text
            )
            return redirect('user_chat_session', chat_request_id=chat_request.id)

    # Get all messages in this chat session
    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')

    return render(request, 'chat/chat_session.html', {
        'messages': messages,
        'chat_request_id': chat_request_id,
        'agent': chat_request.agent.username,  # Use agent's username directly
        'user': chat_request.user  # Pass the user to the template if needed
    })


def agent_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate against the User model
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user is an agent
            try:
                agent = Agent.objects.get(username=username)
                # Log the agent in
                # Use the login function to set the user session
                login(request, user)
                request.session['agent_username'] = agent.username
                agent.set_online()  # Set the agent online
                # Redirect to agent chat requests
                return redirect('agent_chat_requests')
            except Agent.DoesNotExist:
                messages.error(request, "You are not authorized to log in.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'admin/agent_login.html')


@agent_required
def agent_logout_view(request):
    # Get the current agent from the request
    agent = Agent.objects.filter(username=request.user.username).first()

    # Check if the agent exists
    if agent:
        agent.set_offline()

    # Log out the agent
    logout(request)
    return redirect('agent_login')


@agent_required
def agent_chat_requests_view(request):
    # Get the agent associated with the logged-in session
    agent_username = request.session.get('agent_username')
    agent = get_object_or_404(Agent, username=agent_username)

    # Fetch chat requests for this agent that have not been accepted
    chat_requests = ChatRequest.objects.filter(agent=agent, accepted=False)

    # Handle the acceptance of a chat request
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        chat_request = get_object_or_404(
            ChatRequest, id=request_id, agent=agent)
        chat_request.accepted = True
        chat_request.save()
        return redirect('agent_chat_session', chat_request_id=chat_request.id)

    return render(request, 'chat/agent_chat_requests.html', {'chat_requests': chat_requests})


@agent_required
def agent_chat_session_view(request, chat_request_id):
    # Fetch the chat request, ensuring it belongs to the logged-in agent
    chat_request = get_object_or_404(
        ChatRequest, id=chat_request_id, agent__username=request.user.username)

    # Ensure the chat request is accepted
    if not chat_request.accepted:
        return redirect('agent_chat_requests')

    # Handle message sending
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Create a new chat message
            ChatMessage.objects.create(
                session=chat_request,
                sender=request.user,  # Assuming the agent is using the same User model
                message=message_text
            )
            return redirect('agent_chat_session', chat_request_id=chat_request.id)

    # Retrieve all messages for the chat session
    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')

    return render(request, 'chat/chat_session.html', {
        'messages': messages,
        'chat_request_id': chat_request_id,
        # Pass the agent's username for display
        'agent_username': request.user.username
    })


@agent_required
def agent_toggle_status(request):
    agent = get_object_or_404(Agent, username=request.user.username)
    agent.is_online = not agent.is_online
    agent.save()
    return redirect('agent_chat_requests')


def search_suggestions(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        # Search in categories
        categories = Category.objects.filter(name__icontains=query)
        for category in categories:
            results.append({
                'name': category.name,
                'url': category.get_absolute_url()
            })

        # Search in subcategories
        subcategories = SubCategory.objects.filter(name__icontains=query)
        for subcategory in subcategories:
            results.append({
                'name': f"{subcategory.category.name} > {subcategory.name}",
                'url': subcategory.get_absolute_url()
            })

        # Search in products
        products = Product.objects.filter(name__icontains=query)
        for product in products:
            results.append({
                'name': product.name,
                'url': product.get_absolute_url()
            })

        # Search in product variants (if variants are shown)
        variants = ProductVariant.objects.filter(
            size__icontains=query) | ProductVariant.objects.filter(color__icontains=query)
        for variant in variants:
            results.append({
                'name': f"{variant.product.name} - {variant.size} - {variant.color}",
                'url': variant.get_absolute_url()
            })

    return JsonResponse(results, safe=False)


def paginate_queryset(queryset, request):
    """Paginate the queryset based on request parameters."""
    paginator = Paginator(queryset, 15)  # Display 10 products per page
    # Get the page number from the GET request
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def filtered_products(request):
    rating_values = request.GET.getlist('rating')
    selected_ratings = request.GET.getlist('rating')

    rating_values = [int(r) for r in rating_values if r.isdigit()]

    if rating_values:
        products = Product.objects.filter(
            ratings__rating__in=rating_values
        ).distinct()
    else:
        products = Product.objects.all()

    # Pagination
    products = paginate_queryset(products, request)

    context = {
        'products': products,
        'selected_ratings': selected_ratings,
    }
    return render(request, 'product/product_list.html', context)


def filtered_products_by_size(request):
    size_values = request.GET.getlist('size')
    selected_sizes = request.GET.getlist('size')

    if size_values:
        products = Product.objects.filter(
            variants__size__in=size_values
        ).distinct()
    else:
        products = Product.objects.all()

    # Pagination
    products = paginate_queryset(products, request)

    context = {
        'products': products,
        'selected_sizes': selected_sizes,
    }
    return render(request, 'product/product_list.html', context)


def filtered_products_by_price(request):
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()

    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            products = products.filter(
                variants__price__gte=min_price, variants__price__lte=max_price).distinct()
        except ValueError:
            pass

    # Pagination
    products = paginate_queryset(products, request)

    context = {
        'products': products,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'product/product_list.html', context)


def filtered_products_by_subcategory(request):
    subcategory_ids = request.GET.getlist('subcategory')
    subcategory_ids = [id for id in subcategory_ids if id]

    products = Product.objects.all()
    if subcategory_ids:
        products = products.filter(
            subcategory__id__in=subcategory_ids).distinct()

    subcategories = SubCategory.objects.annotate(
        product_count=Count('products'))

    # Pagination
    products = paginate_queryset(products, request)

    context = {
        'products': products,
        'subcategories': subcategories,
        'selected_subcategories': subcategory_ids,
    }
    return render(request, 'product/product_list.html', context)


def filtered_products_by_category(request):
    category_ids = request.GET.getlist('category')
    category_ids = [id for id in category_ids if id]

    products = Product.objects.all()
    if category_ids:
        products = products.filter(category__id__in=category_ids).distinct()

    categories = Category.objects.annotate(product_count=Count('products'))

    # Pagination
    products = paginate_queryset(products, request)

    context = {
        'products': products,
        'categories': categories,
        'selected_categories': category_ids,
    }
    return render(request, 'product/product_list.html', context)


def filtered_products_by_option(request):
    filter_option = request.GET.get('filter', '4')

    products = Product.objects.all()

    if filter_option == '1':
        products = products.filter(top_selling=True)
    elif filter_option == '2':
        products = products.filter(recommended=True)
    elif filter_option == '3':
        products = products.filter(sale=True)

    # Pagination
    products = paginate_queryset(products, request)

    context = {
        'products': products,
        'selected_filter': filter_option,
    }

    return render(request, 'product/product_list.html', context)

# Scraper function with image download


def success_page(request):
    return render(request, 'admin/success_page.html')


def scrape_amazon_product(url):
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.5",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.8",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Accept-Language": "en-US,en;q=0.7",
        },
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.8",
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Accept-Language": "en-US,en;q=0.7",
        },
        {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1",
            "Accept-Language": "en-US,en;q=0.6",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Accept-Language": "en-US,en;q=0.5",
        },
        {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.7",
        }
    ]

    headers = random.choice(headers_list)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Fetch title
        title = soup.find(id='productTitle').get_text(
            strip=True) if soup.find(id='productTitle') else None

        # Fetch price
        price = None
        price_whole = soup.find('span', {'class': 'a-price-whole'})
        price_fraction = soup.find('span', {'class': 'a-price-fraction'})
        if price_whole and price_fraction:
            price = f"{price_whole.get_text(strip=True)}.{price_fraction.get_text(strip=True)}"

        # Fetch image
        image_wrapper = soup.find('div', {'id': 'imgTagWrapperId'})
        image = image_wrapper.find('img')['src'] if image_wrapper else None

        # Fetch brand
        brand = soup.find('a', {'id': 'bylineInfo'}).get_text(
            strip=True) if soup.find('a', {'id': 'bylineInfo'}) else 'No brand'

        # Fetch color
        color = None
        color_select = soup.find('span', {'class': 'selection'})
        if color_select:
            color = color_select.get_text(strip=True)
        else:
            color_options = soup.find_all('span', {'class': 'a-text-bold'})
            if color_options:
                color = ', '.join([color.get_text(strip=True)
                                  for color in color_options])

        # Fetch size
        size = None
        size_select = soup.find('span', {'class': 'a-dropdown-prompt'})
        if size_select:
            size = size_select.get_text(strip=True)
        else:
            size_options = soup.find_all('li', {'class': 'a-dropdown-item'})
            if size_options:
                size = ', '.join([size.get_text(strip=True)
                                 for size in size_options])

        # Ensure required data is available (title, price, and image)
        if title and price and image:
            return {
                'title': title,
                'price': price,
                'image': image,
                'brand': brand,
                'color': color or 'No color',
                'size': size or 'No size'
            }
    return None


def download_image(image_url):
    img_temp = NamedTemporaryFile()  # Removed 'delete=True'
    img_temp.write(requests.get(image_url).content)
    img_temp.flush()

    # Extract filename from URL
    filename = os.path.basename(urlsplit(image_url).path)
    return img_temp, filename

# Function to sanitize price by removing non-numeric characters


# Define a static conversion rate (for demonstration purposes, set this to the latest conversion rate)
USD_TO_INR_CONVERSION_RATE = 83  # Example rate: 1 USD = 83 INR


def sanitize_price(price_string):
    # Remove all non-numeric characters except for periods and commas
    price_cleaned = re.sub(r'[^\d.,]', '', price_string)

    # Replace commas with periods in case the price uses commas as a decimal separator
    price_cleaned = price_cleaned.replace(',', '.')

    # Handle cases with multiple periods by keeping only the first valid decimal point
    if price_cleaned.count('.') > 1:
        # Split the string into parts and recombine using only the first decimal point
        parts = price_cleaned.split('.')
        price_cleaned = parts[0] + '.' + ''.join(parts[1:])

    # Convert cleaned price to decimal
    try:
        price_decimal = Decimal(price_cleaned)
    except InvalidOperation:
        return None  # Handle invalid price format

    # Convert USD price to INR
    price_in_inr = price_decimal * Decimal(USD_TO_INR_CONVERSION_RATE)

    return price_in_inr  # Return the converted price in INR


@user_passes_test(lambda u: u.is_superuser)
def add_amazon_product(request):
    if request.method == 'POST':
        form = AmazonProductForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            product_data = scrape_amazon_product(url)

            if product_data:
                # Ensure title, price, and image are present
                if product_data['title'] and product_data['price'] and product_data['image']:
                    # Create AmazonProduct instance
                    amazon_product = AmazonProduct.objects.create(
                        title=product_data['title'],
                        price=product_data['price'],
                        image=product_data['image'],
                        brand=product_data['brand'],
                        color=product_data['color'],
                        size=product_data['size'],
                        url=url
                    )

                    # Get or create the default Category and SubCategory
                    category, created = Category.objects.get_or_create(
                        name='Cloths')  # Default category: Cloths
                    subcategory, created = SubCategory.objects.get_or_create(
                        name='Default Subcategory', category=category)

                    # Create Product instance from scraped AmazonProduct
                    product = Product.objects.create(
                        name=amazon_product.title,
                        description=amazon_product.brand or 'No description available',
                        category=category,
                        subcategory=subcategory,
                        featured=True,
                        sale=False,
                        top_selling=False,
                        recommended=False
                    )

                    # If there is an image, download it and link to ProductImage
                    if amazon_product.image:
                        img_temp, filename = download_image(
                            amazon_product.image)
                        product_image = ProductImage()
                        product_image.image.save(filename, File(img_temp))
                        product_image.save()
                        product.images.add(product_image)

                    # Check if size and color are available before creating ProductVariant
                    if amazon_product.size and amazon_product.color:
                        try:
                            # Clean and sanitize the price string and convert to INR
                            cleaned_price_inr = sanitize_price(
                                amazon_product.price)
                            if cleaned_price_inr is None:
                                messages.error(
                                    request, "Invalid price format.")
                                return redirect('home')

                            # Log the converted INR price for debugging
                            print(f"Price in INR: {cleaned_price_inr}")

                            # Create the ProductVariant
                            ProductVariant.objects.create(
                                product=product,
                                size=amazon_product.size,
                                color=amazon_product.color,
                                price=cleaned_price_inr,
                                # Assuming original price is the same as scraped price
                                original_price=cleaned_price_inr
                            )
                            print("ProductVariant created successfully!")
                        except InvalidOperation:
                            messages.error(
                                request, "Failed to convert price to a valid decimal.")
                            return redirect('home')
                    else:
                        # Log missing size or color
                        print(
                            f"Missing size or color: Size={amazon_product.size}, Color={amazon_product.color}")
                        messages.error(
                            request, "Product variant data is incomplete (size or color missing).")

                    # Redirect to product list after adding
                    return redirect('success_page')
                else:
                    # Show error message if required fields are missing
                    messages.error(
                        request, "Product data is incomplete. Please ensure the product has a title, price, and image.")
            else:
                # Show error if the product data could not be scraped
                messages.error(
                    request, "Failed to scrape product data from the provided URL.")
    else:
        form = AmazonProductForm()

    return render(request, 'admin/add_amazon_product.html', {'form': form})


def scrape_myntra_product(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')

        product_data = None

        for script in scripts:
            if 'application/ld+json' in str(script):  # Looking for JSON-LD
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, list):
                        for item in json_data:
                            if item.get('@type') == 'Product':
                                product_data = item
                                break
                    elif json_data.get('@type') == 'Product':
                        product_data = json_data
                    if product_data:
                        break
                except json.JSONDecodeError:
                    continue

        if product_data:
            title = product_data.get('name', 'No title available')
            brand = product_data.get('brand', {}).get(
                'name', 'No brand available')
            image = product_data.get('image', 'No image available')
            price = product_data.get('offers', {}).get('price', '0.00')

            # Convert price to Decimal, assuming it's in dollars
            price_decimal = Decimal(price.replace(
                ',', '').strip())  # Clean the price string

            return {
                'title': title,
                'price': price_decimal,
                'image': image,
                'brand': brand,
                'url': url
            }
    return None


def sanitize_price_my(price):
    if isinstance(price, Decimal):
        # Convert Decimal to string before processing
        price_str = str(price)
    else:
        price_str = price

    # Example regex to remove unwanted characters
    cleaned_price = re.sub(r'[^\d.]', '', price_str)
    return Decimal(cleaned_price) if cleaned_price else None


@user_passes_test(lambda u: u.is_superuser)
def add_myntra_product(request):
    if request.method == 'POST':
        form = MyntraProductForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            product_data = scrape_myntra_product(url)

            if product_data:
                # Ensure title, price, and image are present
                if product_data['title'] and product_data['price'] and product_data['image']:
                    # Create MyntraProduct instance
                    myntra_product = MyntraProduct.objects.create(
                        title=product_data['title'],
                        price=product_data['price'],
                        image=product_data['image'],
                        brand=product_data['brand'],
                        url=url
                    )

                    # Get or create the default Category and SubCategory
                    category, created = Category.objects.get_or_create(
                        name='Cloths')  # Default category: Cloths
                    subcategory, created = SubCategory.objects.get_or_create(
                        name='Default Subcategory', category=category)

                    # Create Product instance from scraped MyntraProduct
                    product = Product.objects.create(
                        name=myntra_product.title,
                        description=myntra_product.brand or 'No description available',
                        category=category,
                        subcategory=subcategory,
                        featured=True,
                        sale=False,
                        top_selling=False,
                        recommended=False
                    )

                    # If there is an image, download it and link to ProductImage
                    if myntra_product.image:
                        img_temp, filename = download_image(
                            myntra_product.image)
                        product_image = ProductImage()
                        product_image.image.save(filename, File(img_temp))
                        product_image.save()
                        product.images.add(product_image)

                    # Set default sizes and colors if not provided in product_data
                    sizes = product_data.get(
                        'size', ['S', 'M', 'L', 'XL', 'XXL'])
                    color = product_data.get('color', 'Default Color')

                    try:
                        # Clean and sanitize the price string and convert to INR
                        cleaned_price_inr = sanitize_price_my(
                            myntra_product.price)
                        if cleaned_price_inr is None:
                            messages.error(request, "Invalid price format.")
                            return redirect('home')

                        # Log the converted INR price for debugging
                        print(f"Price in INR: {cleaned_price_inr}")

                        # Create a ProductVariant for each size
                        for size in sizes:
                            ProductVariant.objects.create(
                                product=product,
                                size=size,
                                color=color,
                                price=cleaned_price_inr,
                                # Assuming original price is the same as the scraped price
                                original_price=cleaned_price_inr
                            )
                        print("ProductVariant(s) created successfully!")
                    except InvalidOperation:
                        messages.error(
                            request, "Failed to convert price to a valid decimal.")
                        return redirect('home')

                    # Redirect to product list after adding
                    return redirect('success_page')
                else:
                    # Show error message if required fields are missing
                    messages.error(
                        request, "Product data is incomplete. Please ensure the product has a title, price, and image.")
            else:
                # Show error if the product data could not be scraped
                messages.error(
                    request, "Failed to scrape product data from the provided URL.")
    else:
        form = MyntraProductForm()

    return render(request, 'admin/add_myntra_product.html', {'form': form})


def scrape_ajio_product(url):
    # Set up Chrome options for headless mode and improved performance
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    # Wait up to 10 seconds for elements to load
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(url)

        # Wait for and retrieve product details
        product_title = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'prod-name'))).text
        product_price = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'prod-sp'))).text.replace('₹', '').replace(',', '').strip()
        product_image = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'rilrtl-lazy-img'))).get_attribute('src')
        product_brand = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'brand-name'))).text
        variant_color = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'prod-color'))).text
        variant_size = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'size-variant-item'))).text

        # Convert price to Decimal
        price_decimal = sanitize_price_ajio(product_price)

        return {
            'title': product_title,
            'price': price_decimal,
            'image': product_image,
            'brand': product_brand,
            'color': variant_color,
            'size': variant_size,
            'url': url
        }
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        driver.quit()


def sanitize_price_ajio(price_str):
    cleaned_price = re.sub(r'[^\d.]', '', price_str)
    return Decimal(cleaned_price) if cleaned_price else None


@user_passes_test(lambda u: u.is_superuser)
def add_ajio_product(request):
    if request.method == 'POST':
        form = AjioProductForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            product_data = scrape_ajio_product(url)

            if product_data:
                # Ensure title, price, and image are present
                if product_data['title'] and product_data['price'] and product_data['image']:
                    # Convert the price to a string if it’s a Decimal before sanitization
                    price_str = str(product_data['price']) if isinstance(
                        product_data['price'], Decimal) else product_data['price']

                    # Step 1: Create AjioProduct instance for additional metadata
                    ajio_product = AjioProduct.objects.create(
                        title=product_data['title'],
                        price=price_str,
                        image=product_data['image'],
                        brand=product_data['brand'],
                        color=product_data.get('color', 'Default Color'),
                        size=product_data.get('size', 'Default Size'),
                        url=url
                    )

                    # Step 2: Get or create the default Category and SubCategory
                    category, created = Category.objects.get_or_create(
                        name='Cloths')  # Default category: Cloths
                    subcategory, created = SubCategory.objects.get_or_create(
                        name='Default Subcategory', category=category)

                    # Step 3: Create Product instance from AjioProduct
                    product = Product.objects.create(
                        name=ajio_product.title,
                        description=f"Product from {ajio_product.brand}",
                        category=category,
                        subcategory=subcategory,
                        featured=True,
                        sale=False,
                        top_selling=False,
                        recommended=False
                    )

                    # Step 4: If there is an image, download it and link to ProductImage
                    if ajio_product.image:
                        img_temp, filename = download_image(ajio_product.image)
                        product_image = ProductImage()
                        product_image.image.save(filename, File(img_temp))
                        product_image.save()
                        product.images.add(product_image)

                    # Step 5: Set default sizes and colors if not provided in product_data
                    sizes = product_data.get(
                        'size', ['S', 'M', 'L', 'XL', 'XXL'])
                    color = product_data.get('color', 'Default Color')

                    try:
                        # Step 6: Sanitize and convert price to Decimal
                        # Ensure `sanitize_price_ajio` takes a string
                        cleaned_price_inr = sanitize_price_ajio(price_str)
                        if cleaned_price_inr is None:
                            messages.error(request, "Invalid price format.")
                            return redirect('home')

                        # Create a ProductVariant for each size
                        for size in sizes:
                            ProductVariant.objects.create(
                                product=product,
                                size=size,
                                color=color,
                                # Convert back to Decimal if needed for `ProductVariant`
                                price=Decimal(cleaned_price_inr),
                                original_price=Decimal(cleaned_price_inr)
                            )
                        messages.success(
                            request, "AJIO product and variants added successfully.")
                        return redirect('success_page')
                    except InvalidOperation:
                        messages.error(
                            request, "Failed to convert price to a valid decimal.")
                        return redirect('home')
                else:
                    # Show error if required fields are missing
                    messages.error(
                        request, "Product data is incomplete. Please ensure the product has a title, price, and image.")
            else:
                # Show error if scraping fails
                messages.error(
                    request, "Failed to scrape product data from the provided URL.")
    else:
        form = AjioProductForm()

    return render(request, 'admin/add_ajio_product.html', {'form': form})


def get_flipkart_product_variants(url):
    # Set up Chrome options for headless mode and improved performance
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "--disable-dev-shm-usage")  # Improves stability

    # Initialize the WebDriver with Chrome options
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(url)

        # Extract brand, title, and price
        product_brand = "Brand not found"
        product_title = "Title not found"
        product_price = "0"

        try:
            product_brand = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'mEh187'))
            ).text
        except:
            print("Brand not found.")

        try:
            product_title = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'VU-ZEz'))
            ).text
        except:
            print("Title not found.")

        try:
            product_price = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'Nx9bqj'))
            ).text
        except:
            print("Price not found.")

        # Extract product image URLs
        product_images = []
        try:
            image_elements = driver.find_elements(By.CLASS_NAME, 'gqcSqV')
            for image_element in image_elements:
                img_tag = image_element.find_element(
                    By.TAG_NAME, 'img')  # Locate <img> tag within the div
                img_src = img_tag.get_attribute(
                    'src')  # Get the image source URL
                product_images.append(img_src)
        except:
            print("No images found in gqcSqV class.")

        # Extract color information
        colors = []
        try:
            color_elements = driver.find_elements(
                By.CSS_SELECTOR, '.V3Zflw.QX54-Q.E1E-3Z.dpZEpc')
            for color_element in color_elements:
                color = color_element.text.strip()
                if color:
                    colors.append(color)
        except Exception as e:
            print(f"Error extracting colors: {e}")

        # Use default color if none found
        if not colors:
            colors.append("Default Color")

        # Extract all available sizes
        sizes = []
        try:
            size_elements = driver.find_elements(By.CLASS_NAME, 'aJWdJI')
            for size_element in size_elements:
                size_text = size_element.text.strip()
                if size_text:
                    sizes.append(size_text)
        except Exception as e:
            print(f"Error extracting sizes: {e}")

        # Default sizes if not found
        if not sizes:
            sizes = ["Sizes not found"]

        # Compile product data
        product_data = {
            'brand': product_brand,
            'title': product_title,
            'price': product_price,
            'colors': colors,
            'sizes': sizes,
            'product_images': product_images if product_images else None
        }

        return product_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        driver.quit()


def sanitize_price_flipkart(price_str):
    # Remove any non-numeric characters except for decimal points
    cleaned_price = re.sub(r'[^\d.]', '', price_str)
    return Decimal(cleaned_price) if cleaned_price else None


@user_passes_test(lambda u: u.is_superuser)
def add_flipkart_product(request):
    if request.method == 'POST':
        form = FlipkartProductForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            product_data = get_flipkart_product_variants(url)

            if product_data:
                # Ensure required fields are present
                if product_data['title'] and product_data['price'] and product_data['product_images']:
                    # Sanitize the price directly from product_data
                    cleaned_price = sanitize_price_flipkart(
                        product_data['price'])
                    if cleaned_price is None:
                        messages.error(request, "Invalid price format.")
                        return redirect('home')

                    # Step 1: Create FlipkartProduct instance for metadata
                    flipkart_product = FlipkartProduct.objects.create(
                        title=product_data['title'],
                        price=cleaned_price,
                        image=product_data['product_images'][0] if product_data['product_images'] else None,
                        brand=product_data['brand'],
                        # Use first color as default
                        color=product_data['colors'][0],
                        # Use first size as default
                        size=product_data['sizes'][0],
                        url=url
                    )

                    # Step 2: Get or create the default Category and SubCategory
                    category, _ = Category.objects.get_or_create(name='Cloths')
                    subcategory, _ = SubCategory.objects.get_or_create(
                        name='Default Subcategory', category=category)

                    # Step 3: Create Product instance
                    product = Product.objects.create(
                        name=flipkart_product.title,
                        description=f"Product from {flipkart_product.brand}",
                        category=category,
                        subcategory=subcategory,
                        featured=True,
                        sale=False,
                        top_selling=False,
                        recommended=False
                    )

                    # Step 4: Handle product image
                    if flipkart_product.image:
                        img_temp, filename = download_image(
                            flipkart_product.image)
                        product_image = ProductImage()
                        product_image.image.save(filename, File(img_temp))
                        product_image.save()
                        product.images.add(product_image)

                    # Step 5: Set default sizes and colors if not provided
                    sizes = product_data['sizes'] or [
                        'S', 'M', 'L', 'XL', 'XXL']
                    color = product_data['colors'][0] if product_data['colors'] else 'Default Color'

                    try:
                        # Step 6: Create ProductVariant for each size
                        for size in sizes:
                            ProductVariant.objects.create(
                                product=product,
                                size=size,
                                color=color,
                                price=cleaned_price,
                                original_price=cleaned_price
                            )
                        messages.success(
                            request, "Flipkart product and variants added successfully.")
                        return redirect('success_page')
                    except InvalidOperation:
                        messages.error(
                            request, "Failed to create product variants.")
                        return redirect('home')
                else:
                    # Show error if required fields are missing
                    messages.error(
                        request, "Product data is incomplete. Please ensure the product has a title, price, and image.")
            else:
                # Show error if scraping fails
                messages.error(
                    request, "Failed to scrape product data from the provided URL.")
    else:
        form = FlipkartProductForm()

    return render(request, 'admin/add_flipkart_product.html', {'form': form})


@user_passes_test(lambda u: u.is_superuser)
def add_product_links(request):
    return render(request, 'admin/add_product_links.html')
