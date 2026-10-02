from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail
from django.conf import settings
from grabsomore import permissions

from .forms import (
    CheckoutForm,
    ProductForm,
    ProductReviewForm,
    StockUpdateForm,
    StoreForm,
)
from .models import Order, OrderItem, Product, ProductReview, Store


@permissions.vendor_required
def update_stock(request, product_id):
    """
    Allow a vendor to update product inventory levels.

    Ensures stock quantities remain accurate.
    """
    product = get_object_or_404(
        Product,
        id=product_id,
        vendor=request.user
    )
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)

        print("POST DATA:", request.POST)

        if form.is_valid():
            print("FORM VALID")
            print("OLD STOCK:", product.stock)

            product.stock = form.cleaned_data['stock']
            product.save()

            print("NEW STOCK:", product.stock)

            return redirect('eCommerce:vendor_dashboard')

        else:
            print("FORM ERRORS:", form.errors)
    else:
        form = StockUpdateForm(
            initial={
                'stock':
                product.stock
            }
        )
    return render(
        request,
        'eCommerce/update_stock.html',
        {
            'form': form,
            'product': product
        }
    )


@permissions.vendor_required
def create_store(request):
    """
    Allow a vendor to create a new store.

    The store is automatically associated with
    the currently authenticated vendor.
    """
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.vendor = request.user
            store.save()
            return redirect('/ecommerce/vendor/stores/')
    else:
        form = StoreForm()
    return render(
        request,
        'eCommerce/create_store.html',
        {'form': form}
    )


@permissions.vendor_required
def create_product(request):
    """
    Create a new product for the currently logged-in vendor.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.save()

            return redirect('eCommerce:vendor_products')
    else:
        form = ProductForm()
        form.fields['store'].queryset = \
            Store.objects.filter(vendor=request.user)
    return render(
        request,
        'eCommerce/create_product.html',
        {'form': form}
    )


@login_required
@permissions.vendor_required
def update_product(request, product_id):
    """
    Allow a vendor to update an existing product.

    Only products owned by the current vendor
    may be modified.
    """
    product = get_object_or_404(
        Product,
        id=product_id,
        vendor=request.user
    )

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)

        form.fields['store'].queryset = \
            Store.objects.filter(vendor=request.user)

        if form.is_valid():
            form.save()
            return redirect('eCommerce:vendor_products')

    else:
        form = ProductForm(instance=product)

        form.fields['store'].queryset = \
            Store.objects.filter(vendor=request.user)

    return render(
        request,
        'eCommerce/update_product.html',
        {'form': form, 'product': product}
    )


def user_is_vendor(user):
    """
    Check whether the user belongs to the Vendor group.
    """
    return user.groups.filter(
        name='Vendor'
    ).exists()


def user_is_buyer(user):
    """
    Check whether a user belongs to
    the Buyer role.
    """
    return (
        hasattr(user, 'userprofile')
        and user.userprofile.role in ['BUYER', 'ADMIN']
    )


@login_required
def checkout(request):
    """
    Validates stock availability, creates an order,
    deducts inventory, sends an invoice email,
    and finalises the checkout process.
    """
    if not (
        user_is_buyer(request.user)
        or request.user.userprofile.role == 'ADMIN'
    ):
        return HttpResponseForbidden(
            'Only Buyer or Admin users may access checkout.'
        )
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('eCommerce:main_cart_page')
    cart_items = []
    total_price = Decimal('0.00')
    for product_id, cart_value in cart.items():
        product = get_object_or_404(Product, pk=product_id)
        # Supports either cart['1'] = 2 or
        # cart['1'] = {'quantity': 2}
        if isinstance(cart_value, dict):
            quantity = int(cart_value.get('quantity', 1))
        else:
            quantity = int(cart_value)
        line_total = product.price * quantity
        total_price += line_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Validate stock availability
                for item in cart_items:
                    product = item['product']
                    quantity = item['quantity']

                    if quantity > product.stock:
                        messages.error(
                            request,
                            f"Only {product.stock} units of {product.name} "
                            "are available."
                        )
                        return redirect('eCommerce:checkout')

            order = Order.objects.create(
                buyer=request.user,
                full_name=form.cleaned_data['full_name'],
                delivery_address=form.cleaned_data[
                    'delivery_address'
                ],
                phone_number=form.cleaned_data['phone_number'],
                total_price=total_price,
                status='CONFIRMED'
            )

            # Prevents Negative Stock Deduction
            for item in cart_items:
                product = item['product']
                quantity = item['quantity']

                if product.stock < quantity:
                    messages.error(
                        request,
                        f"Insufficient stock for {product.name}."
                    )
                    return redirect('eCommerce:checkout')

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    price=product.price,
                    quantity=quantity
                )

                # Reduce stock
                product.stock -= quantity
                product.save()

                # Build invoice
                invoice_lines = []
                invoice_lines.append(f"Order Number: {order.id}")
                invoice_lines.append("")
                invoice_lines.append("Items Purchased:")
                invoice_lines.append("-" * 30)
                total = Decimal('0.00')
                for item in cart_items:
                    line_total = (
                        item['product'].price *
                        item['quantity']
                    )
                    total += line_total
                    invoice_lines.append(
                        f"{item['product'].name} "
                        f"x {item['quantity']} "
                        f"= R{line_total:.2f}"
                    )
                invoice_lines.append("")
                invoice_lines.append(f"Total: R{total:.2f}")
                invoice_text = "\n".join(invoice_lines)

                # Send email
                try:
                    send_mail(
                        subject=f"Invoice for Order #{order.id}",
                        message=invoice_text,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[request.user.email],
                        fail_silently=False,
                    )

                except Exception as e:
                    print("EMAIL ERROR:", e)
                request.session['cart'] = {}
                request.session.modified = True
            messages.success(
                request,
                f'Order #{order.id} was placed successfully.'
            )
            return redirect(
                'eCommerce:order_confirmation',
                order_id=order.id
            )
    else:
        form = CheckoutForm(
            initial={
                'full_name': request.user.get_full_name(),
            }
        )
    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(
        request,
        'eCommerce/checkout.html',
        context
    )


@login_required
def order_confirmation(request, order_id):
    """
    Display confirmation details for a completed order.

    Shows order summary and purchase information.
    """
    if not user_is_buyer(request.user):
        return HttpResponseForbidden(
            'Only Buyer users may view Buyer orders.'
        )
    order = get_object_or_404(
        Order,
        id=order_id,
        buyer=request.user
    )
    return render(
        request,
        'eCommerce/order_confirmation.html',
        {'order': order}
    )


@permissions.vendor_required
def my_products(request):
    """Display products owned by the logged-in vendor."""
    products = Product.objects.filter(
        vendor=request.user,
        is_active=True,
        store__is_active=True
    )
    return render(
        request,
        'eCommerce/my_products.html',
        {'products': products}
    )


@permissions.admin_required
def admin_dashboard(request):
    """Display the administrator dashboard."""
    return render(
        request,
        'eCommerce/admin_dashboard.html'
    )


@login_required
def buyer_dashboard(request):
    """Display the buyer dashboard for authenticated buyers."""
    if not hasattr(request.user, "userprofile"):
        return HttpResponseForbidden(
            "No account role has been assigned."
        )
    if request.user.userprofile.role != "BUYER":
        return HttpResponseForbidden(
            "Only Buyer users may access this dashboard."
        )
    return render(
        request,
        "eCommerce/buyer_dashboard.html",
    )


def product_search(request):
    """Search for a product and redirect to its detail page."""
    if request.method == 'POST':
        product_name = request.POST.get('product')
        try:
            product = Product.objects.get(
                name=product_name
            )
            return redirect(
                'eCommerce:product_page',
                product_id=product.id
            )
        except Product.DoesNotExist:
            return render(
                request,
                'eCommerce/product_search.html',
                {
                    'error': 'Product not found'
                }
            )
    return render(
        request,
        'eCommerce/product_search.html'
    )


def change_product_price(request):
    """
    Allow a vendor to update the price of products
    they own.
    """
    user = request.user  # Get the currently logged-in user
    # Check if user has permission to change products
    is_vendor = (
        hasattr(user, 'userprofile')
        and user.userprofile.role == 'VENDOR'
    )
    if is_vendor or user.is_staff:
        if request.method == 'POST':
            # Get product name from form
            product_id = request.POST.get('product')
            product = Product.objects.get(
                id=product_id,
                vendor=request.user
            )
            # Get new price from form
            new_price = request.POST.get('new_price')
            # Check both fields were filled out
            if not product_id or not new_price:
                return render(request, 'eCommerce/change_price.html', {
                    'error': 'Please provide both product and new price.'
                })
            try:
                # Convert new price to a decimal number
                product.price = float(new_price)
                product.save()  # Save updated product price to database
                # After success, redirect user to product page
                return redirect(
                    'eCommerce:product_page',
                    product_id=product.id
                )
            except ValueError:
                # If new price isn't a valid number, show error
                return render(request, 'eCommerce/change_price.html', {
                    'error': 'Invalid price format.'
                })
            except ObjectDoesNotExist:
                # If product name does not exist in database, show error
                return render(request, 'eCommerce/change_price.html', {
                    'error': 'Product not found.'
                })
        # Show form when page is first loaded (GET request)
        products = Product.objects.filter(
            vendor=request.user
        )
        return render(
            request,
            'eCommerce/change_price.html',
            {
                'products': products
            }
        )
    # If user does not have permission, show error
    return render(request, 'eCommerce/change_price.html', {
        'error': 'You do not have permission to change prices.'
    })


def add_item_to_cart(request):
    """Add a product to the shopping cart."""
    print("******** ADD TO CART CALLED ********")
    print("PRODUCT ID =", request.POST.get('product_id'))
    print("QUANTITY =", request.POST.get('quantity'))

    item = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    if not item or not quantity:
        return redirect('eCommerce:main_cart_page')
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1
    cart = request.session.get('cart', {})
    if item in cart:
        cart[item] += quantity
    else:
        cart[item] = quantity
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('eCommerce:main_cart_page')


def retrieve_products(request):
    """Retrieve products from the session shopping cart."""
    products = []
    session = request.session
    # If cart exists in session, load products and their quantities
    if 'cart' in session:
        for item, quantity in session['cart'].items():
            try:
                # Get product from database by ID
                product = Product.objects.get(id=int(item))
                # Add product and quantity as a dictionary to list
                products.append({'product': product, 'quantity': quantity})
            except Product.DoesNotExist:
                # Skip if product not found (may have been deleted)
                pass
    return products


def show_user_cart(request):
    """Display the contents of the shopping cart."""
    # Get list of products and quantities from the session cart
    cart_items = retrieve_products(request)
    total_price = 0  # Start total price at zero
    # Calculate subtotal for each cart item and total price for whole cart
    for item in cart_items:
        subtotal = item['product'].price * item['quantity']
        item['subtotal'] = subtotal  # Add subtotal to item dictionary
        total_price += subtotal
    # Render cart page, passing in items and total price
    return render(request, 'eCommerce/main_cart_page.html', {
        'cart': cart_items,
        'total_price': total_price,
    })


def list_products(request):
    """
    Display all available marketplace products.

    Supports customer browsing and product discovery.
    """
    # Get all products from database
    products = Product.objects.filter(is_active=True, store__is_active=True)
    # Show products list page, passing products to template
    return render(
        request,
        'eCommerce/products_list.html',
        {'products': products}
    )


def clear_cart(request):
    """
    Empty the cart by setting session cart to empty dictionary
    Redirect to cart page after clearing
    """
    request.session['cart'] = {}
    request.session.modified = True  # Mark session as changed
    return redirect('eCommerce:main_cart_page')


@permissions.vendor_required
def vendor_dashboard(request):
    """
    Display vendor statistics, stores and product
    information.
    """
    products = Product.objects.filter(
        vendor=request.user,
        is_active=True,
        store__is_active=True
    )
    stores = Store.objects.filter(
        vendor=request.user,
        is_active=True
    )
    low_stock = products.filter(
        stock__lt=10
    ).count()
    context = {
        'store_count': stores.count(),
        'product_count': products.count(),
        'low_stock_count': low_stock,
        'sales_total': 0.00
    }
    return render(
        request,
        'eCommerce/vendor_dashboard.html',
        context
    )


@login_required
def add_review(request, product_id):
    """
    Allow a customer to submit a review for a product.

    Prevents duplicate reviews and records
    purchase verification status.
    """
    if not user_is_buyer(request.user):
        return HttpResponseForbidden(
            "Only buyers may submit product reviews."
        )
    product = get_object_or_404(Product, id=product_id)
    has_purchased = OrderItem.objects.filter(
        order__buyer=request.user,
        product=product
    ).exists()

    if request.method == "POST":
        form = ProductReviewForm(request.POST)
        print("FORM TYPE:", type(form))
        print("FORM FIELDS:", form.fields.keys())
        if form.is_valid():
            existing_review = ProductReview.objects.filter(
                product=product,
                user=request.user
            ).first()
            if existing_review:
                messages.error(
                    request,
                    "You have already reviewed this product."
                )
                return redirect(
                    'eCommerce:product_page',
                    product_id=product.id
                )
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            has_purchased = OrderItem.objects.filter(
                order__buyer=request.user,
                product=product
            ).exists()
            review.verified_purchase = has_purchased
            print("USER:", request.user)
            print("PRODUCT:", product.id)
            print("HAS PURCHASED:", has_purchased)
            print("ABOUT TO SAVE REVIEW")
            review.save()
            print("REVIEW SAVED:", review.id)
            if existing_review:
                print("EXISTING REVIEW FOUND")
            if form.is_valid():
                print("FORM VALID")
            else:
                print("FORM INVALID")
                print(form.errors)
            return redirect(
                "eCommerce:product_page",
                product_id=product.id,
            )
        print("FORM IS INVALID")
        print("POST DATA:", request.POST)
        print("FORM ERRORS:", form.errors.as_data())
        reviews = ProductReview.objects.filter(
            product=product
        ).select_related("user")
        return render(
            request,
            "eCommerce/product_page.html",
            {
                "product": product,
                "review_form": form,  # Important
                "reviews": reviews,
                "is_buyer": True,
                "is_vendor": False,
            },
        )
    return redirect(
        "eCommerce:product_page",
        product_id=product.id,
    )


def view_product_page(request, product_id):
    """
    Display detailed information for a specific product.

    Includes pricing, stock availability,
    reviews, and review submission options.
    """
    product = get_object_or_404(
        Product,
        id=product_id,
    )
    reviews = ProductReview.objects.filter(
        product=product
    ).select_related("user").order_by("-id")
    review_count = reviews.count()
    context = {
        "product": product,
        "reviews": reviews,
        "review_form": ProductReviewForm(),
        "review_count": review_count,
        "is_buyer": (
            request.user.is_authenticated
            and user_is_buyer(request.user)
        ),
        "is_vendor": (
            request.user.is_authenticated
            and user_is_vendor(request.user)
        ),
    }
    return render(
        request,
        "eCommerce/product_page.html",
        context,
    )


def user_list(request):
    """Display all registered users."""
    users = User.objects.all()
    return render(
        request,
        'eCommerce/user_list.html',
        {'users': users}
    )


def vendor_list(request):
    """Display all vendor accounts."""
    vendors = User.objects.filter(
        groups__name='Vendor'
    )
    return render(
        request,
        'eCommerce/vendor_list.html',
        {'vendors': vendors}
    )


def order_list(request):
    """Display all customer orders."""
    orders = Order.objects.all().order_by('-id')
    return render(
        request,
        'eCommerce/order_list.html',
        {
            'orders': orders,
        },
    )


@login_required
def store_list(request):
    """Display all active (non soft deleted)
    vendor stores"""
    stores = Store.objects.filter(
        vendor=request.user,
        is_active=True,
    )
    return render(
        request,
        'eCommerce/store_list.html',
        {'stores': stores},
    )


@login_required
def products_list(request):
    """
    Display all available marketplace products.

    Supports customer browsing and product discovery.
    """
    products = Product.objects.filter(
        store__vendor=request.user,
        store__is_active=True
    )
    return render(
        request,
        'eCommerce/product_list.html',
        {'products': products}
    )


@login_required
def vendor_products(request):
    """
    Display products owned by the logged-in vendor.
    """
    products = Product.objects.filter(
        vendor=request.user,
        store__is_active=True,
    )

    return render(
        request,
        'eCommerce/vendor_products.html',
        {
            'products': products
        }
    )


@permissions.vendor_required
def delete_product(request, product_id):
    """
    Permanently delete a vendor-owned product.
    """

    product = get_object_or_404(
        Product,
        id=product_id,
        vendor=request.user
    )

    if request.method == "POST":

        try:
            product_name = product.name
            product.delete()

            messages.success(
                request,
                f"{product_name} has been permanently deleted."
            )

        except ProtectedError:

            messages.error(
                request,
                "This product cannot be deleted because it exists in one or "
                "more orders."
            )

        return redirect('eCommerce:vendor_products')

    return render(
        request,
        'eCommerce/delete_product.html',
        {'product': product}
    )


@permissions.vendor_required
def update_store(request, store_id):
    """
    Update details for an existing vendor store.

    Ensures only the store owner can make changes.
    """
    store = get_object_or_404(
        Store,
        id=store_id,
        vendor=request.user
    )
    if request.method == "POST":
        form = StoreForm(
            request.POST,
            instance=store
        )
        if form.is_valid():
            form.save()
            return redirect('/ecommerce/vendor/stores/')
    else:
        form = StoreForm(instance=store)
    return render(
        request,
        'eCommerce/update_store.html',
        {
            'form': form,
            'store': store
        }
    )


@permissions.vendor_required
def delete_store(request, store_id):
    """
    Permanently delete a vendor-owned store.
    """

    store = get_object_or_404(
        Store,
        id=store_id,
        vendor=request.user
    )

    if request.method == "POST":

        store_name = store.name
        store.delete()

        messages.success(
            request,
            f"{store_name} has been permanently deleted."
        )

        return redirect('/ecommerce/vendor/stores/')

    return render(
        request,
        'eCommerce/delete_store.html',
        {'store': store}
    )
