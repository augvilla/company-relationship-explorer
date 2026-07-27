# Company Relationship Explorer

Enter a stock ticker and get its full company name, current price, today's
% change, sector, and country (all live from Yahoo Finance) — plus
AI-generated estimates of its main competitors, suppliers, and customers.

## Important: the competitor/supplier/customer data is unverified

Real supply-chain relationship data (who actually supplies or buys from
whom) is proprietary — it's what products like Bloomberg SPLC or FactSet
Supply Chain Relationships charge institutions for. There's no free,
reliable public source for it.

This app instead asks an AI model to give its best-informed estimate,
clearly labeled as such in the app. Treat these three columns as a
starting point for research, not as verified fact — always confirm
independently before relying on them for anything real.

## Setup

This app calls the Anthropic API to generate those estimates, so it needs
its own API key (get one at https://console.anthropic.com), separate from
the login gate's allowed-users list. Add both to Streamlit secrets — see
`.streamlit/secrets.toml.example` for the format. Without a key, the app
still works for price/sector/country, it just skips the relationship
section.

## Access

This app is private and limited to approved users.

---

Created by Augustine Villalobos
