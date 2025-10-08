from rest_framework import serializers
from .models import WhitelistedIP, BlockedIP

class WhitelistedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhitelistedIP
        fields = ['id', 'ip', 'added_by', 'date_added', 'reason']
        read_only_fields = ['id', 'added_by', 'date_added']

    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user
        return super().create(validated_data)

class BlockedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedIP
        fields = ['id', 'ip', 'reason', 'blocked_at', 'blocked_by']
        read_only_fields = ['id', 'blocked_by', 'blocked_at']

    def create(self, validated_data):
        validated_data['blocked_by'] = self.context['request'].user
        return super().create(validated_data)