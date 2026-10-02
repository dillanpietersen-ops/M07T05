from django import forms
from .models import Product, ProductReview, Store


class ProductForm(forms.ModelForm):
    """
    Form used by vendors to create and update products.
    """
    class Meta:
        model = Product
        fields = [
            'store',
            'name',
            'description',
            'price',
            'stock',
        ]


class StoreForm(forms.ModelForm):
    """
    Form used by vendors to create and manage stores.
    """
    class Meta:
        model = Store
        fields = ['name', 'description']


class ProductReviewForm(forms.ModelForm):
    """
    Form for customers to submit product reviews
    and ratings.
    """

    class Meta:
        model = ProductReview
        fields = ["rating", "comment"]

        widgets = {
            "rating": forms.Select(
                choices=[
                    (1, "★"),
                    (2, "★★"),
                    (3, "★★★"),
                    (4, "★★★★"),
                    (5, "★★★★★"),
                ]
            ),
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "form-control",
                }
            ),
        }


class CheckoutForm(forms.Form):
    """
    Captures customer delivery and contact details
    required to complete an order.
    """
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    delivery_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )


class StockUpdateForm(forms.Form):
    """
    Form used by vendors to update product stock.
    """

    stock = forms.IntegerField(
        min_value=0
    )
