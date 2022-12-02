import json

from colander.core.models import *


class Enrichment:
    def __init__(self):
        self.registry = {}

    def resolve_id(self, id):
        if id in self.registry:
            return self.registry.get(id)
        return id

    def import_observable_from_dict(self, elt, case_id, owner_id):
        """
        Example of JSON:
        {
          "id": "d313596b-3dd3-43dc-b49a-aae46c612ee4",
          "extracted_from": "ac734fd4-d688-4031-be86-eec649a102ed",
          "obj_type": "observable",
          "type": "domain",
          "value": "5to3dze6izf2porimw4wryt6vi.appsync-api.eu-west-1.amazonaws.com"
        }

        :param elt: element to be imported
        :param case_id: ID the case this observable belongs to
        :returns a tuple containing the suggested ID and the saved ID
        """
        observable_type = ObservableType.objects.get(short_name=elt.get('type').upper())
        exists, o = Observable.get_if_exists(elt.get('value'), case_id)

        if exists:
            o = o.first()

        if not exists:
            o = Observable(
                id=elt.get('id'),
                case_id=case_id,
                type=observable_type,
                value=elt.get('value'),
                owner_id=owner_id
            )
            extracted_from = elt.get('extracted_from', None)
            if extracted_from:
                o.extracted_from_id = extracted_from
            o.save()

        self.registry[elt.get('id')] = str(o.id)
        return elt.get('id'), str(o.id)

    def import_observable_relation_from_dict(self, elt, case_id, owner_id):
        """
        Example of JSON:
        {
          "id": "0bdf85b3-2d9e-42a2-94ea-77535b79499e",
          "obj_type": "relation",
          "name": "resolves",
          "from": "5f976968-0024-4afa-aef5-1665666d2ae8",
          "to": "7d863fe2-6b18-4ca7-983e-28a4487bfc6b"
        }

        :param elt: element to be imported
        :param case_id: ID the case this observable belongs to
        :param owner_id: ID of the user who created this object
        :returns a tuple containing the suggested ID and the saved ID
        """
        exists, o = ObservableRelation.get_if_exists(elt.get('name'), case_id, elt.get('from'), elt.get('to'))

        if exists:
            o = o.first()

        if not exists:
            o = ObservableRelation(
                id=elt.get('id'),
                case_id=case_id,
                name=elt.get('name'),
                owner_id=owner_id,
                observable_from_id=self.resolve_id(elt.get('from')),
                observable_to_id=self.resolve_id(elt.get('to')),
            )
            o.save()

        self.registry[elt.get('id')] = str(o.id)
        return elt.get('id'), str(o.id)

    def import_event_from_dict(self, elt, case_id, owner_id):
        """
        Example of JSON:
        {
            "id": "8c6439d8-53a4-4a76-9b0b-1bc1f7762894",
            "obj_type": "event",
            "type": "communication",
            "name": "10.0.0.16 -> 179.60.192.36",
            "first_seen": "2022-01-07T19:01:36.177000",
            "last_seen": "2022-01-07T19:02:07.312000",
            "extracted_from": "ac734fd4-d688-4031-be86-eec649a102ed",
            "involved_observables": [
                "7ff7ff2f-3225-41bf-b22d-9ed4de1270d0",
                "2ae41658-57df-4d47-8939-bc7fc30eaf2b",
                "006fa9c4-85bf-4a32-81ab-4d2d56883de6",
                "5f976968-0024-4afa-aef5-1665666d2ae8",
                "7d863fe2-6b18-4ca7-983e-28a4487bfc6b"
            ],
            "attributes": [
                {
                  "community_id": "1:ZLaTwXX59t3oeOsLjlRlCrzayBw="
                }
            ]
        }

        :param elt: element to be imported
        :param case_id: ID the case this observable belongs to
        :param owner_id: ID of the user who created this object
        :returns a tuple containing the suggested ID and the saved ID
        """
        event_type = EventType.objects.get(short_name=elt.get('type').upper())
        exists, o = Event.get_if_exists(elt.get('name'), case_id)

        if exists:
            o = o.first()

        if not exists:
            o = Event(
                id=elt.get('id'),
                case_id=case_id,
                type=event_type,
                name=elt.get('name'),
                owner_id=owner_id,
                count=elt.get('count', 0),
                first_seen=elt.get('first_seen'),
                last_seen=elt.get('last_seen'),
            )
            extracted_from = elt.get('extracted_from', None)
            if extracted_from:
                o.extracted_from_id = extracted_from
            o.save()
            involved_observables = elt.get('involved_observables', None)
            if involved_observables:
                for observable in involved_observables:
                    o.involved_observables.add(observable)
                    pass
            attributes = elt.get('attributes', None)
            attrs = {}
            if attributes:
                for attr in attributes:
                    for k, v in attr.items():
                        attrs[k] = v
                o.attributes = attrs
            o.save()

        self.registry[elt.get('id')] = str(o.id)
        return elt.get('id'), str(o.id)

    def import_json(self, json_string, case_id, owner_id):
        json_data = json.loads(json_string)
        for elt in json_data:
            obj_type = elt.get('obj_type')
            if obj_type == 'observable':
                # import observable from dict
                self.import_observable_from_dict(elt, case_id, owner_id)
            elif obj_type == 'relation':
                # import relation from dict
                self.import_observable_relation_from_dict(elt, case_id, owner_id)
            elif obj_type == 'event':
                # import event from dict
                self.import_event_from_dict(elt, case_id, owner_id)


def t1():
    json_string = """
        [
    {
      "id": "7d863fe2-6b18-4ca7-983e-28a4487bfc6b",
      "extracted_from": "ac734fd4-d688-4031-be86-eec649a102ed",
      "obj_type": "observable",
      "type": "domain",
      "value": "www.facebook.com"
    },{
      "id": "8c6439d8-53a4-4a76-9b0b-1bc1f7762894",
      "obj_type": "event",
      "type": "communication",
      "name": "10.0.0.16 -> 179.60.192.36",
      "first_seen": "2022-01-07T19:01:36.177000",
      "last_seen": "2022-01-07T19:02:07.312000",
      "extracted_from": "ac734fd4-d688-4031-be86-eec649a102ed",
      "involved_observables": [
        "7ff7ff2f-3225-41bf-b22d-9ed4de1270d0",
        "2ae41658-57df-4d47-8939-bc7fc30eaf2b",
        "006fa9c4-85bf-4a32-81ab-4d2d56883de6",
        "5f976968-0024-4afa-aef5-1665666d2ae8",
        "7d863fe2-6b18-4ca7-983e-28a4487bfc6b"
      ],
      "attributes": [
        {
          "community_id": "1:ZLaTwXX59t3oeOsLjlRlCrzayBw="
        },
        {
          "application_category_name": "SocialNetwork"
        },
        {
          "application_confidence": "6"
        },
        {
          "application_is_guessed": "0"
        },
        {
          "application_name": "TLS.Facebook"
        },
        {
          "bidirectional_bytes": "12219"
        },
        {
          "bidirectional_duration_ms": "31135"
        },
        {
          "bidirectional_first_seen_ms": "1641578496177"
        },
        {
          "bidirectional_last_seen_ms": "1641578527312"
        },
        {
          "bidirectional_packets": "31"
        },
        {
          "client_fingerprint": "d8c87b9bfde38897979e41242626c2f3"
        },
        {
          "content_type": ""
        },
        {
          "dst2src_bytes": "4587"
        },
        {
          "dst2src_duration_ms": "31123"
        },
        {
          "dst2src_first_seen_ms": "1641578496177"
        },
        {
          "dst2src_last_seen_ms": "1641578527300"
        },
        {
          "dst2src_packets": "15"
        },
        {
          "dst_ip": "179.60.192.36"
        },
        {
          "dst_mac": "42:a6:81:bb:05:70"
        },
        {
          "dst_oui": "42:a6:81"
        },
        {
          "dst_port": "443"
        },
        {
          "expiration_id": "0"
        },
        {
          "id": "0"
        },
        {
          "ip_version": "4"
        },
        {
          "protocol": "6"
        },
        {
          "requested_server_name": "www.facebook.com"
        },
        {
          "server_fingerprint": "4ef1b297bb817d8212165a86308bac5f"
        },
        {
          "src2dst_bytes": "7632"
        },
        {
          "src2dst_duration_ms": "31135"
        },
        {
          "src2dst_first_seen_ms": "1641578496177"
        },
        {
          "src2dst_last_seen_ms": "1641578527312"
        },
        {
          "src2dst_packets": "16"
        },
        {
          "src_ip": "10.0.0.16"
        },
        {
          "src_mac": "d4:38:9c:b9:78:5c"
        },
        {
          "src_oui": "d4:38:9c"
        },
        {
          "src_port": "38195"
        },
        {
          "tunnel_id": "0"
        },
        {
          "user_agent": ""
        },
        {
          "vlan_id": "0"
        }
      ]
    }]
    """
    case_id = '137f7000-be59-4a58-bfab-cd459e9377da'
    # e = Enrichment()
    # e.import_json(json_string, case_id, 1)
    # import_observable_from_dict(json.loads(json_string), case_id, 1)
