from rest_framework import serializers
from .models import Expense, Category, PaymentMethod, PaymentType
from accounts.models import CustomUser
from datetime import datetime, timedelta
import uuid


def get_first_monday(year, month):
    """Calculate the first Monday of a given month, handling special case when 1st is Monday"""
    first_day = datetime(year, month, 1).date()
    if first_day.weekday() == 0:  # Monday
        return first_day + timedelta(days=7)  # Next Monday (8th)
    else:
        days_to_monday = (7 - first_day.weekday()) % 7
        return first_day + timedelta(days=days_to_monday)


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
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    payment_method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())
    payment_type = serializers.PrimaryKeyRelatedField(queryset=PaymentType.objects.all())

    class Meta:
        model = Expense
        fields = [
            'id', 'user', 'date', 'name', 'amount', 'category', 'payment_method',
            'payment_type', 'description', 'is_credit', 'total_credit_amount',
            'installments', 'current_installment', 'remaining_amount',
            'credit_group_id', 'subscription', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('is_credit'):
            if not data.get('total_credit_amount'):
                raise serializers.ValidationError("total_credit_amount is required for credit expenses")
            if not data.get('installments') or data['installments'] < 1:
                raise serializers.ValidationError("installments must be at least 1 for credit expenses")
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = CategorySerializer(instance.category).data
        data['payment_method'] = PaymentMethodSerializer(instance.payment_method).data
        data['payment_type'] = PaymentTypeSerializer(instance.payment_type).data
        return data

    def create(self, validated_data):
        user = validated_data.pop('user', None) or self.context['request'].user

        if validated_data.get('is_credit'):
            # Handle credit expense creation
            total_credit_amount = validated_data['total_credit_amount']
            installments = validated_data['installments']
            amount_per_installment = total_credit_amount / installments
            credit_group_id = str(uuid.uuid4())
            date = validated_data['date']
            name = validated_data['name']
            custom_description = validated_data.get('description', '')

            # Create installment 0
            expense_0 = Expense.objects.create(
                user=user,
                date=date,
                name=f"{name} - Cuota 0/{installments}",
                amount=0,
                category=validated_data['category'],
                payment_method=validated_data['payment_method'],
                payment_type=validated_data['payment_type'],
                description=f"{custom_description} Monto total={total_credit_amount} Cantidad de cuotas={installments}".strip(),
                is_credit=True,
                total_credit_amount=total_credit_amount,
                installments=installments,
                current_installment=0,
                remaining_amount=total_credit_amount,
                credit_group_id=credit_group_id
            )

            # Create installments 1 to N
            start_year = date.year
            start_month = date.month + 1
            if start_month > 12:
                start_month = 1
                start_year += 1

            for i in range(1, installments + 1):
                installment_month = start_month + (i - 1)
                installment_year = start_year
                while installment_month > 12:
                    installment_month -= 12
                    installment_year += 1

                installment_date = get_first_monday(installment_year, installment_month)

                Expense.objects.create(
                    user=user,
                    date=installment_date,
                    name=f"{name} - Cuota {i}/{installments}",
                    amount=amount_per_installment,
                    category=validated_data['category'],
                    payment_method=validated_data['payment_method'],
                    payment_type=validated_data['payment_type'],
                    description=f"Cuota {i} de {installments}",
                    is_credit=True,
                    total_credit_amount=total_credit_amount,
                    installments=installments,
                    current_installment=i,
                    remaining_amount=total_credit_amount - (amount_per_installment * i),
                    credit_group_id=credit_group_id
                )

            return expense_0
        else:
            validated_data['user'] = user
            return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'telegram_chat_id', 'user_type']