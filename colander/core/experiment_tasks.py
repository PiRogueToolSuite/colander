import base64
import binascii
import datetime
import json
import re
import subprocess
import tempfile
from binascii import hexlify

import communityid
import requests
from django.utils import timezone
from elasticsearch_dsl import Index
from yara import StringMatchInstance

from colander.core.es_utils import geoip_pipeline_id
from colander.core.models import DetectionRule, PiRogueExperiment, PiRogueExperimentAnalysis

external_packages = [
    'com.android.org.conscrypt.',
    'com.android.okhttp.',
    'okhttp3.internal.',
    'okhttp3.logging.',
    'java.util.',
    'java.util.',
    'java.io.',
    'java.lang.',
    'android.os.',
]


def enrich_stack_trace(trace):
    if 'stack' not in trace['data']:
        return
    stack = trace['data']['stack']
    for call in stack:
        clazz = call.get('class')
        call['is_external'] = False
        for package in external_packages:
            if clazz.startswith(package):
                call['is_external'] = True
                break


def _clean_ip_address(ip):
    if ip.startswith('::ffff:') and ip.count('.') == 3:
        return ip.replace('::ffff:', '')
    return ip


def compute_community_id(trace):
    cid = communityid.CommunityID()
    src_ip = _clean_ip_address(trace['data']['local_ip'])
    src_port = trace['data']['local_port']
    dst_ip = _clean_ip_address(trace['data']['dest_ip'])
    dst_port = trace['data']['dest_port']

    if 'tcp' in trace['data']['socket_type']:
        tpl = communityid.FlowTuple.make_tcp(src_ip, dst_ip, src_port, dst_port)
    else:
        tpl = communityid.FlowTuple.make_udp(src_ip, dst_ip, src_port, dst_port)

    return {
        'src_ip': src_ip,
        'src_port': src_port,
        'dst_ip': dst_ip,
        'dst_port': dst_port,
        'community_id': cid.calc(tpl)
    }


def build_stack_traces(socket_trace_file):
    with open(socket_trace_file) as f:
        socket_traces = json.load(f)
    community_id_stack_trace = {}
    traces = []

    for trace in socket_traces:
        flow_data = compute_community_id(trace)
        enrich_stack_trace(trace)
        trace['data']['local_ip'] = flow_data.get('src_ip')
        trace['data']['dest_ip'] = flow_data.get('dst_ip')
        trace['data']['community_id'] = flow_data.get('community_id')
        traces.append(trace)
        if flow_data.get('community_id') not in community_id_stack_trace:
            community_id_stack_trace[flow_data.get('community_id')] = trace

    return community_id_stack_trace, traces


def get_stack_trace(traces, community_id, timestamp, operations):
    best_guess = None
    min_time = 99999999
    for t in traces:
        if t['data']['community_id'] == community_id and t['data']['socket_event_type'] in operations:
            # print('Found -----')
            trace_timestamp = t['timestamp']
            delta = abs(int(trace_timestamp) - int(timestamp))
            if delta < min_time:
                min_time = delta
                best_guess = t
    print(f'Best guess with delta {min_time/1000} for {community_id}, {timestamp}, {operations}')
    return best_guess

def _compact_stack_trace(trace):
    clean_stack = []
    stack = trace['data']['stack']
    for call in stack:
        clazz = call.get('class')
        if clazz not in clean_stack:
            clean_stack.append(clazz)
    return clean_stack


def parse_ip_layer(ip_layer: dict):
    try:
        return {
                   'ip': ip_layer.get('ip_ip_src'),
                   'host': ip_layer.get('ip_ip_src_host')
               }, {
                   'ip': ip_layer.get('ip_ip_dst'),
                   'host': ip_layer.get('ip_ip_dst_host'),
               }
    except Exception:
        return None


def parse_eth_layer(eth_layer: dict):
    return {
               'mac': eth_layer.get('eth_eth_src')
           }, {
               'mac': eth_layer.get('eth_eth_dst'),
           }


def parse_sll_layer(sll_layer: dict):
    return {
               'mac': sll_layer.get('sll_sll_src_eth')
           }, {
               'mac': None,
           }


def parse_single_http2_layer(http2_layer: dict):
    data, headers, raw_data = None, None, ''
    if 'http2_http2_body_reassembled_data' in http2_layer:
        raw_data = http2_layer.get('http2_http2_body_reassembled_data', '')
        if type(raw_data) is list:
            raw_data = ':'.join(http2_layer.get('http2_http2_body_reassembled_data', ''))
        raw_data = raw_data.replace(':', '')

        data = binascii.unhexlify(raw_data)
        try:
            data = data.decode('utf-8')
        except Exception:
            data = raw_data
    elif 'http2_http2_data_data' in http2_layer:
        raw_data = http2_layer.get('http2_http2_data_data', '')
        if type(raw_data) is list:
            raw_data = ':'.join(http2_layer.get('http2_http2_data_data', ''))
        raw_data = raw_data.replace(':', '')

        data = binascii.unhexlify(raw_data)
        try:
            data = data.decode('utf-8')
        except Exception:
            data = raw_data

    if 'http2_http2_headers' in http2_layer:
        header_name = http2_layer.get('http2_http2_header_name')
        header_value = http2_layer.get('http2_http2_header_value')
        if len(header_name) != len(header_value):
            print('ERROR http2 unmatched header names with values')
            return headers, data, raw_data
        headers = dict([x for x in zip(header_name, header_value)])
    return headers, data, raw_data


def parse_http2(layers: dict, layer_names: list):
    to_return = []
    http2_layer = layers.get('http2')
    if type(http2_layer) is list:
        for l in http2_layer:
            headers, data, raw_data = parse_single_http2_layer(l)
            to_return.append({
                'headers': headers,
                'raw_data': raw_data,
                'data': data
            })
    else:
        headers, data, raw_data = parse_single_http2_layer(http2_layer)
        to_return.append({
            'headers': headers,
            'raw_data': raw_data,
            'data': data
        })
    return to_return


def parse_http3(layers: dict, layer_names: list):
    headers, data = None, None
    http3_layer = layers.get('http3')
    # if type(http_layer) is list:
    #    for l in http_layer:
    #        parse_single_http_layer(l)
    # else:
    #    parse_single_http2_layer(http2_layer)
    return headers, data


def parse_http(layers: dict, layer_names: list):
    headers, data, raw_data = None, None, ''
    print(layers.keys())
    http_layer = layers.get('http')
    if http_layer and type(http_layer) is list:  # list in case of websocket communication
        http_layer = http_layer[0]
    data = http_layer.get('http_http_file_data', '')
    raw_data = data
    raw_headers = None
    if 'http_http_response_line' in http_layer:
        raw_headers = http_layer.get('http_http_response_line')
    if 'http_http_request_line' in http_layer:
        raw_headers = http_layer.get('http_http_request_line')
    headers = {}
    for line in raw_headers:
        i = line.find(': ')
        name = line[:i].strip()
        value = line[i + 1:].strip()
        headers[name] = value
    if 'http_http_response_for_uri' in http_layer:
        headers['uri'] = http_layer.get('http_http_response_for_uri')
    elif 'http_http_request_full_uri' in http_layer:
        headers['uri'] = http_layer.get('http_http_request_full_uri')

    if 'data' in http_layer:
        data_layer = http_layer.get('data')
        if data_layer:
            raw_data = ''
            if type(data_layer) is dict:
                data_layer = [data_layer]
            for d in data_layer:
                raw_data += d.get('data_data_data', '').replace(':', '')
    elif 'media' in layers:
        data_layer = layers.get('media').get('media_media_type')
        if data_layer:
            raw_data = data_layer.replace(':', '')
    elif 'mime_multipart' in layers:
        data_layer = layers.get('mime_multipart').get('data')
        if data_layer:
            raw_data = ''
            if type(data_layer) is dict:
                data_layer = [data_layer]
            for d in data_layer:
                raw_data += d.get('data_data_data').replace(':', '')
    elif 'data' in layers:
        data_layer = layers.get('data')
        if data_layer:
            raw_data = ''
            if type(data_layer) is dict:
                data_layer = [data_layer]
            for d in data_layer:
                raw_data += d.get('data_data_data', '').replace(':', '')

    return [{'headers': headers, 'data': data, 'raw_data': raw_data}]

    # 'http_http_request_line' // request headers
    # 'http_http_request_method'
    # 'http_http_request_full_uri'
    # 'http_http_file_data' // data if sent

    # 'http_http_response_code' (+ 'http_http_response_code_desc' pour lisibilité)
    # 'http_http_response_line' // response headers
    # 'http_http_response_for_uri' // uri which replies
    # 'http_http_file_data'

    # if type(http_layer) is list:
    #    for l in http_layer:
    #        parse_single_http_layer(l)
    # else:
    #    parse_single_http2_layer(http2_layer)


def get_top_most_layers(packet, protocol, protocol_stack):
    i = protocol_stack.find(f':{protocol}')
    top_most_layer_names = protocol_stack[i + 1:].split(':')
    top_most_layers = {k: packet.get('layers').get(k) for k in top_most_layer_names}
    return top_most_layers, top_most_layer_names


def dispatch(packet):
    protocol_stack = packet.get('layers').get('frame').get('frame_frame_protocols')
    packets = []
    packet_description = {
        'src': {},
        'dst': {},
        'timestamp': packet.get('timestamp'),
        'protocol': packet.get('protocol', ''),
        'source': packet.get('source', ''),
        'destination': packet.get('destination', ''),
        'length': packet.get('length', -1),
        'community_id': packet.get('layers').get('communityid_communityid'),
        'headers': None,
        'data': None,
        'raw_data': None,
        'protocol_stack': protocol_stack
    }
    if 'ip' not in packet.get('layers'):
        return None

    src_ip, dst_ip = parse_ip_layer(packet.get('layers').get('ip'))
    if protocol_stack.startswith('eth:'):
        src_eth, dst_eth = parse_eth_layer(packet.get('layers').get('eth'))
    if protocol_stack.startswith('sll:'):
        src_eth, dst_eth = parse_sll_layer(packet.get('layers').get('sll'))
    packet_description['src'].update(src_ip)
    packet_description['src'].update(src_eth)
    packet_description['dst'].update(dst_ip)
    packet_description['dst'].update(dst_eth)

    if ':http3' in protocol_stack:
        top_most_layers, top_most_layer_names = get_top_most_layers(packet, 'http3', protocol_stack)
        parse_http3(top_most_layers, top_most_layer_names)
        return
    elif ':http2' in protocol_stack:
        top_most_layers, top_most_layer_names = get_top_most_layers(packet, 'http2', protocol_stack)
        ret = parse_http2(top_most_layers, top_most_layer_names)
        for r in ret:
            pd = packet_description.copy()
            # pd['headers'] = []
            pd['data'] = ''
            if r['headers']:
                pd['headers'] = [(k, str(v)) for k, v in r['headers'].items()]
            if r['data']:
                pd['data'] = r['data']
            if r['raw_data']:
                pd['raw_data'] = r['raw_data']
            packets.append(pd)
        return packets
    elif ':http' in protocol_stack:
        top_most_layers, top_most_layer_names = get_top_most_layers(packet, 'http', protocol_stack)
        ret = parse_http(top_most_layers, top_most_layer_names)
        for r in ret:
            pd = packet_description.copy()
            # pd['headers'] = []
            pd['data'] = ''
            if r['headers']:
                pd['headers'] = [(k, str(v)) for k, v in r['headers'].items()]
            if r['data']:
                pd['data'] = r['data']
            if r['raw_data']:
                pd['raw_data'] = r['raw_data']
            packets.append(pd)
        return packets


def attach_aes_information(aes_traces, packet, field='raw_data'):
    packet_raw_data = packet.get(field)
    packet['aes_info'] = {
        'decrypted': '',
        'alg': '',
        'iv': '',
        'key': ''
    }
    for aes_trace in aes_traces:
        data = aes_trace.get('data')
        if not packet_raw_data:
            continue
        if len(data.get('in'))<16 or len(data.get('out'))<16:
            continue
        if data.get('in') in packet_raw_data or packet_raw_data in data.get('in'):
            packet['aes_info'] = {
                'decrypted': data.get('out'),
                'alg': data.get('alg'),
                'iv': data.get('iv'),
                'key': data.get('key')
            }
            return True
        elif data.get('out') in packet_raw_data or packet_raw_data in data.get('out'):
            packet['aes_info'] = {
                'decrypted': data.get('in'),
                'alg': data.get('alg'),
                'iv': data.get('iv'),
                'key': data.get('key')
            }
            return True
    return False


def get_detected_tracker(tracker_definitions, stack_trace):
    for _, tracker in tracker_definitions.get('trackers').items():
        code_sig = tracker.get('code_signature')
        if len(code_sig) <4:
            continue
        p = re.compile(code_sig, re.IGNORECASE)
        for trace in stack_trace:
            if p.match(trace):
                return {
                    'name': tracker.get('name'),
                    'categories': tracker.get('categories'),
                }
    return None



def save_decrypted_traffic(pirogue_dump_id):
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    pirogue_dump = PiRogueExperiment.objects.get(id=pirogue_dump_id)

    index_name = f'{pirogue_dump.get_es_index()}'
    try:
        index = Index(index_name)
        if index.exists():
            index.delete()
        if not index.exists():
            index.create()
            PiRogueExperimentAnalysis.init(index=index_name)
    except Exception as e:
        print(e)

    pcap = 'pcap.file'
    ssl_keylog = 'sslkeylog.file'
    socket_trace = 'socket_trace.file'
    aes_trace = 'aes_trace.file'
    pcapng = 'xx_decrypted_traffic.pcapng'
    json_traffic = 'xx_json_traffic.json'

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Get all the files
        with open(f'{tmp_dir}/{pcap}', mode='wb') as out:
            for chunk in pirogue_dump.pcap.file.chunks():
                out.write(chunk)
        with open(f'{tmp_dir}/{ssl_keylog}', mode='wb') as out:
            for chunk in pirogue_dump.sslkeylog.file.chunks():
                out.write(chunk)
        with open(f'{tmp_dir}/{socket_trace}', mode='wb') as out:
            for chunk in pirogue_dump.socket_trace.file.chunks():
                out.write(chunk)
        if pirogue_dump.aes_trace:
            with open(f'{tmp_dir}/{aes_trace}', mode='wb') as out:
                for chunk in pirogue_dump.aes_trace.file.chunks():
                    out.write(chunk)
        # Generate the PCAPNG file
        try:
            subprocess.check_call(
                f'editcap --inject-secrets tls,{tmp_dir}/{ssl_keylog} {tmp_dir}/{pcap} {tmp_dir}/{pcapng}',
                shell=True
            )
        except Exception as e:
            print(e)
            return

        # Generate the JSON file containing the traffic
        try:
            subprocess.check_call(
                # f'tshark -2 -T ek --enable-protocol communityid -Ndmn -r {tmp_dir}/{pcapng} > {tmp_dir}/{json_traffic}',
                f'tshark -2 -T ek -PVx --enable-protocol communityid  -R "http or http2 or quic" -Ndmn -r {tmp_dir}/{pcapng} > {tmp_dir}/{json_traffic}',
                shell=True
            )
        except Exception as e:
            print(e)
            return

        socket_traces_file = f'{tmp_dir}/{socket_trace}'
        socket_traces, traces  = build_stack_traces(socket_traces_file)

        aes_traces = []
        if pirogue_dump.aes_trace:
            aes_traces_file = f'{tmp_dir}/{aes_trace}'
            with open(aes_traces_file) as aes:
                aes_traces = json.load(aes)

        tracker_definitions = {}
        response = requests.get('https://reports.exodus-privacy.eu.org/api/trackers')
        if response.status_code == 200:
            tracker_definitions = response.json()

        time_windows = {}

        with open(f'{tmp_dir}/{json_traffic}') as traffic_json_file:
            for line in traffic_json_file.readlines():
                if line.startswith('{"timestamp":'):
                    packet = json.loads(line)
                    c_id = packet.get('layers').get('communityid_communityid')
                    p_timestamp = packet.get('timestamp')
                    if c_id not in time_windows:
                        time_windows[c_id] = []
                    time_windows[c_id].append(p_timestamp)
                    d = dispatch(packet)
                    if not d:
                        continue
                    for p in d:
                        try:
                            if p.get('data') or True:
                                p['experiment_id'] = pirogue_dump_id
                                if socket_traces and p.get('community_id') in socket_traces:
                                    operations = ['write', 'sendto']
                                    if '10.8.0.' in packet.get('destination'):
                                        operations = ['read', 'recvfrom']
                                    full_stack_trace = get_stack_trace(traces, p.get('community_id'), p.get('timestamp'), operations)
                                    p['full_stack_trace'] = full_stack_trace
                                    p['stack_trace'] = _compact_stack_trace(full_stack_trace)
                                is_json = False
                                try:
                                    data = json.loads(p.get('data'))
                                    p['data'] = json.dumps(data, indent=2)
                                    is_json = True
                                except:
                                    pass
                                try:
                                    if not is_json:
                                        data = base64.b64decode(p.get('data').replace('\n', '').strip())
                                        if data:
                                            p['data'] = hexlify(data).decode('utf-8')
                                except:
                                    pass
                                if aes_traces:
                                    if not attach_aes_information(aes_traces, p, field='raw_data'):
                                        attach_aes_information(aes_traces, p, field='data')
                                if tracker_definitions:
                                    t = get_detected_tracker(tracker_definitions, p['stack_trace'])
                                # Save in ES
                                analysis = PiRogueExperimentAnalysis()
                                analysis.owner = str(pirogue_dump.owner_id)
                                analysis.case_id = str(pirogue_dump.case_id)
                                analysis.experiment_id = str(pirogue_dump.id)
                                analysis.analysis_date = timezone.now()
                                analysis.result = p
                                if t:
                                    analysis.tracker = t
                                analysis.timestamp = datetime.datetime.utcfromtimestamp(int(p['timestamp']) / 1000.0)
                                analysis.save(index=index_name, pipeline=geoip_pipeline_id)
                        except Exception as e:
                            print('Oooooops')
                            print(e)


def _extract_matching_snippet(match: StringMatchInstance, content):
    content_length = len(content)
    context = 64
    match_off_start = match.offset
    match_off_end = match_off_start + match.matched_length
    snippet_off_start = max(0, match_off_start - context)
    snippet_off_end = min(content_length, match_off_end + context)
    snippet = content[snippet_off_start:match_off_start] + '<mark>' + content[match_off_start:match_off_end] + '</mark>' + content[match_off_end:snippet_off_end]
    return snippet

def apply_detection_rules(pirogue_dump_id):
    import yara
    from elasticsearch_dsl import connections
    connections.create_connection(hosts=['elasticsearch'], timeout=20)
    pirogue_dump: PiRogueExperiment = PiRogueExperiment.objects.get(id=pirogue_dump_id)
    detection_rules: list[DetectionRule] = DetectionRule.get_user_detection_rules(pirogue_dump.owner, pirogue_dump.case)
    print(len(detection_rules))
    analysis = pirogue_dump.analysis
    for record in analysis:
        matches = []
        content = record.decoded_data if record.decoded_data else record.result.data
        whole_content = ''
        if hasattr(record.result, 'headers') and record.result.headers:
            for k, v in record.result.headers:
                whole_content += f'{k}: {v}\n'
        whole_content += '\n' + content
        for rule in detection_rules:
            if rule.type.short_name == 'YARA':
                try:
                    compiled_rule = yara.compile(source=rule.content)
                except Exception as e:
                    print(e)
                    continue

                rule_matches = compiled_rule.match(data=whole_content)
                match_objects = []
                for match in rule_matches:
                    match_object = {
                        'rule_id': str(rule.id),
                        'rule': match.rule,
                        'tags': match.tags,
                        'strings': [],
                    }
                    for s in match.strings:
                        instances = []
                        for i in s.instances:
                            instances.append(_extract_matching_snippet(i, whole_content))
                        match_object['strings'].append({
                            'identifier': s.identifier,
                            'instances': instances,
                        })
                        match_objects.append(match_object)
                matches.extend(match_objects)
                print(rule_matches)
                record.detections['yara'] = matches
                record.save()

