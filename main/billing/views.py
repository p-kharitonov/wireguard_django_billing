from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.shortcuts import get_object_or_404

from billing.serializers import UserSerializer, WireguardPeerSerializer, DNSSerializer, AllowedNetworksSerializer
from billing.models import User
from django_wireguard.models import WireguardPeer, WireguardDNS, WireguardAllowedNetworks


def get_user(telegram_id):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None


class UserListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, telegram_id, *args, **kwargs):
        user_instance = get_user(telegram_id)
        if not user_instance:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.query_params.get('type') == "check_add_peer":
            status_check, text = user_instance.check_for_adding_peer()
            if not status_check:
                return Response({'permit': status_check, 'text': text}, status=status.HTTP_200_OK)
            else:
                payment = user_instance.get_new_payment_for_adding_peer()
                balance = user_instance.get_new_balance_for_adding_peer()
                activity_until = user_instance.get_new_date_activity_until_for_adding_peer()
                cost = user_instance.get_cost_for_adding_peer()
                result = {'permit': status_check,
                    'cost_of_per_excess_peer': user_instance.tariff.cost_of_per_excess_peer,
                    'payment': payment,
                    'balance': balance,
                    'activity_until': activity_until,
                    'cost': cost}
                return Response(result, status=status.HTTP_200_OK)
        elif request.query_params.get('type') == "download":
            peer_id = request.query_params.get('peer_id')
            peer = user_instance.peers.filter(pk=peer_id).first()
            if peer:
                result = {'name': peer.name, 'config': peer.get_config()}
                return Response(result, status=status.HTTP_200_OK)
        else:
            serializer = UserSerializer(user_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)


class PeerListAllApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        peers = WireguardPeer.objects.all().order_by('name',)
        serializer = WireguardPeerSerializer(peers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        telegram_id = request.data['telegram_id']
        user_instance = get_user(telegram_id)
        print(user_instance)
        if not user_instance:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        peer = user_instance.add_peer()
        serializer = WireguardPeerSerializer(peer)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

class PeerListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, telegram_id):
        try:
            return User.objects.get(telegram_id=telegram_id).peers
        except User.DoesNotExist:
            return None

    def get(self, request, telegram_id, *args, **kwargs):
        peers = self.get_queryset(telegram_id)
        serializer = WireguardPeerSerializer(peers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PeerDetailApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return WireguardPeer.objects.get(pk=pk)
        except WireguardPeer.DoesNotExist:
            return None

    def get(self, request, pk, *args, **kwargs):
        peer = get_object_or_404(WireguardPeer, pk=pk)
        serializer = WireguardPeerSerializer(peer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        peer = get_object_or_404(WireguardPeer, pk=pk)
        data = {}
        if 'dns_id' in request.data:
            data['dns'] = request.data['dns_id']
        if 'allowed_networks_id' in request.data:
            data['allowed_networks'] = request.data['allowed_networks_id']
        if 'update_keys' in request.data:
            peer.update_keys()
            return Response(data=WireguardPeerSerializer(peer).data, status=status.HTTP_201_CREATED)

        serializer = WireguardPeerSerializer(instance=peer, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

class DNSListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        dns = WireguardDNS.objects.all()
        serializer = DNSSerializer(dns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AllowedNetworksListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        allowed_networks = WireguardAllowedNetworks.objects.all()
        serializer = AllowedNetworksSerializer(allowed_networks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

