import { getSnodeSignatureParams } from '../src/crypto/signature';
import type { KeyPair } from 'libsodium-wrappers-sumo';
import sodium from 'libsodium-wrappers-sumo';
import { mnemonicToSeedSync } from 'bip39';

async function testSignature() {
  await sodium.ready;

  // Values from the Python logs
  const mnemonic = "right indoor flower blood exchange cheese wonder gossip system sheriff spell scale roast";
  const seed = mnemonicToSeedSync(mnemonic);
  
  const ed25519Key: KeyPair = sodium.crypto_sign_seed_keypair(seed.slice(0, 32));

  const testVector = {
    method: 'retrieve',
    namespace: 2,
    timestamp: 1752458289343,
  };

  // We need to override the timestamp generation in getSnodeSignatureParams
  // for a deterministic test vector.
  const originalDateNow = Date.now;
  Date.now = () => testVector.timestamp;

  const signatureParams = getSnodeSignatureParams({
    ed25519Key: ed25519Key,
    method: testVector.method as 'retrieve',
    namespace: testVector.namespace,
  });

  Date.now = originalDateNow; // Restore original Date.now

  console.log("--- TypeScript Signature Generation ---");
  console.log("Mnemonic:", mnemonic);
  console.log("Timestamp:", testVector.timestamp);
  console.log("Namespace:", testVector.namespace);
  console.log("Generated Signature:", signatureParams.signature);
  console.log("Generated pubkeyEd25519:", signatureParams.pubkeyEd25519);
  console.log("------------------------------------");
}

testSignature();
