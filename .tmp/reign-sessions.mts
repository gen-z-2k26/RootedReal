const key = process.env.REIGN_API_KEY || "";
const r = await fetch(
  "https://api.reign.com/v1/transactions?from=2026-11-12&to=2026-11-12&pageSize=3",
  { headers: { Authorization: `Bearer ${key}` } },
);
console.log("transactions", r.status, (await r.text()).slice(0, 6000));
