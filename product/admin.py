from django.urls import reverse
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import (
    Cart,
    CartItem,
    Category,
    SubCategory,
    Product,
    ProductVariant,
    ProductImage,
    ProductLabel,
    Profile,
    SiteSetting,
    Wishlist,
    AmazonProduct,
    DiscountCode,
    Inventory,

    BillingAddress,
    ShippingAddress,

    DynamicPriceField,
    Order,
    OrderItem,
    Rating,
    Invoice,
    Ticket,
    TicketReply,
    Agent,
    ChatRequest,
    ChatMessage,
    ProblemRequest,
    Discount,
    AjioProduct,
    FlipkartProduct

)
from django.contrib import admin
from product.forms import TicketReplyForm


# Resource classes for each model
class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category


class SubCategoryResource(resources.ModelResource):
    class Meta:
        model = SubCategory


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product


class ProductVariantResource(resources.ModelResource):
    class Meta:
        model = ProductVariant


class ProductImageResource(resources.ModelResource):
    class Meta:
        model = ProductImage


class ProductLabelResource(resources.ModelResource):
    class Meta:
        model = ProductLabel


class ProfileResource(resources.ModelResource):
    class Meta:
        model = Profile


class SiteSettingResource(resources.ModelResource):
    class Meta:
        model = SiteSetting


class WishlistResource(resources.ModelResource):
    class Meta:
        model = Wishlist


class CartResource(resources.ModelResource):
    class Meta:
        model = Cart


class CartItemResource(resources.ModelResource):
    class Meta:
        model = CartItem


class InventoryResource(resources.ModelResource):
    class Meta:
        model = Inventory


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'color', 'price',)


class ProductLabelInline(admin.TabularInline):
    model = ProductLabel
    extra = 1
    fields = ('label', 'value')


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ('name',)


@admin.register(SubCategory)
class SubCategoryAdmin(ImportExportModelAdmin):
    resource_class = SubCategoryResource
    list_display = ('name', 'category')


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ('name', 'category', 'subcategory')
    filter_horizontal = ('images',)
    inlines = [ProductVariantInline, ProductLabelInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(ImportExportModelAdmin):
    resource_class = ProductVariantResource
    list_display = ('product', 'size', 'color', 'price',)
    readonly_fields = ('product',)


@admin.register(ProductImage)
class ProductImageAdmin(ImportExportModelAdmin):
    resource_class = ProductImageResource
    list_display = ('image',)


@admin.register(ProductLabel)
class ProductLabelAdmin(ImportExportModelAdmin):
    resource_class = ProductLabelResource
    list_display = ('product', 'label', 'value')


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    resource_class = ProfileResource
    list_display = ('user', 'mobile')


@admin.register(SiteSetting)
class SiteSettingAdmin(ImportExportModelAdmin):
    resource_class = SiteSettingResource
    list_display = ('site_title', 'logo', 'updated_at')


@admin.register(Wishlist)
class WishlistAdmin(ImportExportModelAdmin):
    resource_class = WishlistResource
    list_display = ('user', 'product_count', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'

    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username',)

    class ProductInline(admin.TabularInline):
        model = Wishlist.products.through
        extra = 1

    inlines = [ProductInline]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('get_total_price',)


class CartAdmin(ImportExportModelAdmin):
    resource_class = CartResource
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    inlines = [CartItemInline]


class CartItemAdmin(ImportExportModelAdmin):
    resource_class = CartItemResource
    list_display = ('cart', 'product_variant', 'quantity',
                    'get_total_price')
    search_fields = ('cart__user__username', 'product_variant__name')
    list_filter = ('product_variant',)


@admin.register(Inventory)
class InventoryAdmin(ImportExportModelAdmin):
    resource_class = InventoryResource
    list_display = ('product', 'stock')
    search_fields = ('product__name',)


# Register the models with the admin site
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(DiscountCode)
admin.site.register(ShippingAddress)
admin.site.register(BillingAddress)


admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Rating)
admin.site.register(AmazonProduct)

admin.site.register(DynamicPriceField)
admin.site.register(Invoice)

admin.site.register(AjioProduct)


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    form = TicketReplyForm
    extra = 1
    readonly_fields = ('created_at',)
    can_delete = False


class TicketAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'status',
                    'created_at', 'view_chat_link')
    inlines = [TicketReplyInline]

    def view_chat_link(self, obj):
        url = reverse('ticket-chat', args=[obj.id])
        return format_html('<a href="{}">View Chat</a>', url)

    view_chat_link.short_description = 'Chat'


admin.site.register(Ticket, TicketAdmin)


class AgentAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ('username', 'name', 'phone', 'is_online')
    # Enable searching by these fields
    search_fields = ('username', 'name', 'phone')
    list_filter = ('is_online',)  # Enable filtering by 'is_online' status


admin.site.register(Agent, AgentAdmin)
admin.site.register(ChatRequest)
admin.site.register(ChatMessage)
admin.site.register(ProblemRequest)
admin.site.register(FlipkartProduct)


@admin.register(Discount)
class ProductLabelAdmin(ImportExportModelAdmin):
    pass


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('variant', 'discount_type',
                    'discount_value', 'start_date', 'end_date')
