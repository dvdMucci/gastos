from rest_framework import serializers
from .models import Income, IncomeCategory, IncomeSource
from accounts.models import CustomUser


class IncomeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeCategory
        fields = ['id', 'name', 'icon', 'color', 'is_active']


class IncomeSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeSource
        fields = ['id', 'name', 'icon', 'color', 'is_active']


class IncomeSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=IncomeCategory.objects.all())
    source = serializers.PrimaryKeyRelatedField(queryset=IncomeSource.objects.all())

    class Meta:
        model = Income
        fields = [
            'id', 'user', 'date', 'amount', 'description', 'cotizacion_dolar', 'en_dolares',
            'category', 'source', 'is_recurring', 'recurring_frequency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate recurring fields
        if data.get('is_recurring') and not data.get('recurring_frequency'):
            raise serializers.ValidationError("recurring_frequency is required for recurring income")
        if not data.get('is_recurring') and data.get('recurring_frequency'):
            raise serializers.ValidationError("recurring_frequency should not be set for non-recurring income")

        # Validate amount
        if data.get('amount', 0) <= 0:
            raise serializers.ValidationError("Amount must be positive")

        # Validate date (no future dates)
        from django.utils import timezone
        if data.get('date') and data['date'] > timezone.now().date():
            raise serializers.ValidationError("Future dates are not allowed")

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category'] = IncomeCategorySerializer(instance.category).data
        data['source'] = IncomeSourceSerializer(instance.source).data
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'telegram_chat_id', 'user_type']