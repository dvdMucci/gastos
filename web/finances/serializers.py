from rest_framework import serializers
from .models import Expense, Category, PaymentMethod, PaymentType
from accounts.models import CustomUser


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'color', 'is_active']


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'icon']


class PaymentTypeSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = PaymentType
        fields = ['id', 'name', 'payment_method', 'is_default']


class ExpenseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    payment_type = PaymentTypeSerializer(read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'user', 'date', 'name', 'amount', 'category', 'payment_method',
            'payment_type', 'description', 'is_credit', 'total_credit_amount',
            'installments', 'current_installment', 'remaining_amount',
            'credit_group_id', 'subscription', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'telegram_chat_id', 'user_type']