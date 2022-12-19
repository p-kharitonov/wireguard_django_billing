from typing import List


def purge_private_keys() -> int:
    """
    Purge all Private Key from database.

    :return: Removed keys count.
    """
    from django_wireguard.models import WireguardPeer

    peers = WireguardPeer.objects.filter(private_key__isnull=False)
    if peers.exists():
        peers.update(private_key=None)

    return peers.count()


def clean_comma_separated_list(value: str) -> List[str]:
    """
    Clean comma separated list of values.

    Removes all spaces and newlines (CR, CRLF, LF chars).
    Removes trailing commas.
    Returns empty list if string is empty after evaluation.

    :value: comma-separated list of values
    :type value: str
    :return: list of values separated and trimmed from input
    :rtype: list
    """
    values = (value
              .replace(' ', ',')
              .replace('\r', ',')
              .replace('\n', ',')
              .rstrip(',')
              .split(','))

    if values == ['']:
        return []
    return list(filter(None, values))


def clean_comma_separated_str(value: str) -> str:
    """
    Clean comma separated string of values.

    Removes all spaces and newlines (CR, CRLF, LF chars).
    Removes trailing commas.
    Returns empty list if string is empty after evaluation.

    :value: comma-separated string of values
    :type value: str
    :return: string of values separated and trimmed from input
    :rtype: string
    """

    return ','.join(clean_comma_separated_list(value))
