import { getPaymentAccounts, maskSecret, reignMode } from "../lib/payment-config";
const a = await getPaymentAccounts({ fresh: true });
const r = a.reign;
console.log({
  blobPath: process.env.PAYMENT_CONFIG_BLOB_PATH || "(default)",
  managed: a.managed,
  enabled: r.enabled,
  mode: reignMode(r.secretKey, r.publishableKey),
  publishableKey: r.publishableKey || "(empty)",
  secretKey: maskSecret(r.secretKey) || "(empty)",
  webhookSecret: maskSecret(r.webhookSecret) || "(empty)",
  scriptSrc: r.scriptSrc || "(empty)",
  scriptIntegrity: r.scriptIntegrity || "(empty)",
});
