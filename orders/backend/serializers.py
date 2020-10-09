from rest_framework import serializers
from .models import User, Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True) 

    class Meta:
        model = User 
        fields = ('id', 'first_name', 'last_name', 'email', 'username', 'company', 'position', 'contacts')
        read_only_fields = ('id', )
