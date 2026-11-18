import Stripe from "stripe";
import { getPaymentAccounts } from "../lib/payment-config";
const a = await getPaymentAccounts({ fresh: true });
const stripe = new Stripe(a.stripe.secretKey);
try {
  const pi = await stripe.paymentIntents.create({ amount: 100, currency: "usd", automatic_payment_methods: { enabled: true, allow_redirects: "always" }, excluded_payment_method_types: ["affirm","afterpay_clearpay","klarna"] as never });
  console.log("stripe PI ok", pi.id, pi.status, pi.payment_method_types);
  await stripe.paymentIntents.cancel(pi.id);
} catch (e) { console.log("stripe PI FAIL", (e as Error).message); }
const acct = await stripe.accounts.retrieve().catch((e) => ({ err: e.message }));
console.log("stripe account", JSON.stringify(acct).slice(0, 300));
const base = a.paypal.mode === "live" ? "https://api-m.paypal.com" : "https://api-m.sandbox.paypal.com";
const t = await (await fetch(`${base}/v1/oauth2/token`, { method: "POST", headers: { Authorization: "Basic " + Buffer.from(`${a.paypal.clientId}:${a.paypal.clientSecret}`).toString("base64"), "Content-Type": "application/x-www-form-urlencoded" }, body: "grant_type=client_credentials" })).json();
const o = await fetch(`${base}/v2/checkout/orders`, { method: "POST", headers: { Authorization: `Bearer ${t.access_token}`, "Content-Type": "application/json" }, body: JSON.stringify({ intent: "CAPTURE", purchase_units: [{ reference_id: "probe", custom_id: "probe", amount: { currency_code: "USD", value: "1.00" } }] }) });
console.log("paypal order", o.status, (await o.text()).slice(0, 200));
