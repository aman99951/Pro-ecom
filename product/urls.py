from django.urls import path
from product import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('guest/', views.guest_checkout, name='guest_checkout'),

    path('product-list', views.product_list, name="product_list"),
    path('products/', views.filtered_products, name='filtered_products'),
    path('products/size/', views.filtered_products_by_size,
         name='filtered_products_by_size'),
    path('products/price/', views.filtered_products_by_price,
         name='filtered_products_by_price'),
    path('products/subcategory/', views.filtered_products_by_subcategory,
         name='filtered_products_by_subcategory'),
    path('products/category/', views.filtered_products_by_category,
         name='filtered_products_by_category'),
    path('products/filter', views.filtered_products_by_option,
         name='filtered_products_by_option'),


    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    path('product-cart', views.view_cart, name='view_cart'),


    path('wishlist/toggle/<int:product_id>/',
         views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/remove/<int:product_id>/',
         views.remove_from_wishlist, name='remove_from_wishlist'),

    path('add-to-cart/<int:variant_id>/',
         views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/',
         views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/',
         views.update_cart_item, name='update_cart_item'),
    path('profile/', views.profile_view, name='profile'),
    path('checkout/', views.checkout, name='checkout'),

    path('order-success/<int:order_id>/',
         views.order_success, name='order_success'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/cancel/<int:order_id>/',
         views.cancel_order, name='cancel_order'),
    path('add-billing-address/', views.add_billing_address,
         name='add_billing_address'),
    path('add-shipping-address/', views.add_shipping_address,
         name='add_shipping_address'),

    path('order/<int:order_id>/reorder/', views.reorder, name='reorder'),

    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('order/<int:order_id>/create_invoice/',
         views.create_invoice, name='create_invoice'),
    path('invoice/<int:invoice_id>/mark_paid/',
         views.mark_invoice_as_paid, name='mark_invoice_as_paid'),
    path('invoice/<int:invoice_id>/cancel/',
         views.cancel_invoice, name='cancel_invoice'),

    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('list/', views.ticket_list, name='ticket_list'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/<int:ticket_id>/chat/',
         views.TicketChatView.as_view(), name='ticket-chat'),

    path('sales-report/', views.sales_report, name='sales_report'),


    path('chat-request/', views.user_chat_request_view, name='user_chat_request'),
    path('agent-requests/', views.agent_chat_requests_view,
         name='agent_chat_requests'),
    path('chat-session/<int:chat_request_id>/',
         views.user_chat_session_view, name='user_chat_session'),
    path('agent-chat-session/<int:chat_request_id>/',
         views.agent_chat_session_view, name='agent_chat_session'),
    path('toggle-status/', views.agent_toggle_status, name='agent_toggle_status'),
    path('submit-problem/', views.user_chat_request_view,
         name='submit_problem_description'),

    path('search-suggestions/', views.search_suggestions,
         name='search_suggestions'),

    path('agent/login/', views.agent_login_view, name='agent_login'),
    path('agent/logout/', views.agent_logout_view, name='agent_logout'),

    path('add/', views.add_amazon_product, name='add_amazon_product'),
    path('add-myntra-product/', views.add_myntra_product,
         name='add_myntra_product'),
    path('add-ajio-product/', views.add_ajio_product, name='add_ajio_product'),
    path('success/', views.success_page, name='success_page'),
    path('add-flipkart-product/', views.add_flipkart_product,
         name='add_flipkart_product'),
    path('add-products/', views.add_product_links, name='add_product_links'),

]
