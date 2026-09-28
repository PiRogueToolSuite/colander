# colander/core/tests/security/test_archive_signing_key_overwrite.py
import json
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from django.test import Client, TestCase
from django.urls import reverse

from colander.core.models import Case
from colander.users.models import User

def _make_keypair():
    """Return (private_key, private_pem, public_pem) matching Case.generate_key_pair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode('utf-8')
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('utf-8')
    return private_key, private_pem, public_pem

class TestArchiveSigningKeyOverwrite(TestCase):
    password = ['8F7JbzWGES8hH4zWM6R1MPPCI5', '8F7JbzWGES8hH4zWM6R1MPPCI6']

    @classmethod
    def setUpTestData(cls):
        # User 1
        cls.user1 = User.objects.create_user(username='u1', password=cls.password[0])
        cls.case1 = Case.objects.create(name='c1', owner=cls.user1, description='xx')
        # User 2 (attacker)
        cls.user2 = User.objects.create_user(username='u2', password=cls.password[1])

    def _remap_url(self, case):
        return reverse(
            'archives_remap_entity_view',
            kwargs={'super_type': 'Case', 'uuid': str(case.id)},
        )

    def test_attacker_overwrites_case_signing_key_and_forges_signature(self):
        attacker_sk, attacker_sk_pem, attacker_pk_pem = _make_keypair()
        original_sk = self.case1.signing_key
        original_pk = self.case1.public_key
        client = Client()
        client.login(username=self.user2.username, password=self.password[1])

        # Exploit: PATCH u1's Case via the archive-import remap endpoint
        payload = {
            'signing_key': attacker_sk_pem,
            'public_key': attacker_pk_pem,
        }
        response = client.post(
            self._remap_url(self.case1),
            data=json.dumps(payload),
            content_type='application/json',
        )
        print(f"Response status: {response.status_code}")
        print(f"Response       : {response}")
        self.assertNotEqual(response.status_code, 200, "IDOR: attacker access entity")
        self.case1.refresh_from_db()

        self.assertEqual(self.case1.signing_key, original_sk, "signing_key overwritten")
        self.assertEqual(self.case1.public_key, original_pk, "public_key overwritten")

        # Impact: forge a detached signature the way Artifact.sign() does
        digest = hashes.Hash(hashes.SHA256())
        digest.update(b'attacker-controlled evidence')
        sha256_hex = digest.finalize().hex()
        forged_sig = attacker_sk.sign(
            bytes.fromhex(sha256_hex),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            utils.Prehashed(hashes.SHA256()),
        )
        case_pk = serialization.load_pem_public_key(self.case1.public_key.encode('utf-8'))
        try:
            case_pk.verify(
                forged_sig,
                bytes.fromhex(sha256_hex),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                utils.Prehashed(hashes.SHA256()),
            )
            self.assertFalse(True, "attacker-forged signature verifies against the case key")
        except InvalidSignature:
            pass

        self.assertEqual(self.case1.signing_key, original_sk, "signing_key overwritten")
        self.assertEqual(self.case1.public_key, original_pk, "public_key overwritten")
