---
title: "IANA Example Domains"
source: "https://www.iana.org/help/example-domains"
kind: "url"
captured_at: "2026-05-25T14:09:04.719450+00:00"
tags:
  - iana
  - example-domains
  - reserved-domains
  - documentation
  - dns
---

# IANA Example Domains

> IANA explains that domains like example.com and example.org are reserved for documentation and should not be depended on for production HTTP service.

## TL;DR

- Domains such as `example.com` and `example.org` are maintained for documentation purposes.
- These domains are described in RFC 2606 and RFC 6761.
- They may be used as illustrative examples in documents without prior coordination with IANA.
- They are not available for registration or transfer.
- IANA provides best-effort web service on example domain hosts to explain their purpose.
- Applications should not require example domains to have operating HTTP service.

## Key claims & findings

- “As described in RFC 2606 and RFC 6761,” some domains including `example.com` and `example.org` are maintained for documentation purposes.
- These domains “may be used as illustrative examples in documents without prior coordination with us.”
- The example domains “are not available for registration or transfer.”
- IANA provides “a web service on the example domain hosts” with “basic information on the purpose of the domain.”
- The web services are “provided as best effort” and “are not designed to support production applications.”
- IANA expects “incidental traffic for incorrectly configured applications.”
- IANA explicitly says: “please do not design applications that require the example domains to have operating HTTP service.”
- Further reading listed: “IANA-managed Reserved Domains.”
- Last revised: `2017-05-13`.
- IANA functions “coordinate the Internet’s globally unique identifiers” and are provided by Public Technical Identifiers, an affiliate of ICANN.

## Entities & links

- [[IANA]]
- [[Example Domains]]
- [[example.com]]
- [[example.org]]
- [[RFC 2606]]
- [[RFC 6761]]
- [[IANA-managed Reserved Domains]]
- [[Domain Names]]
- [[Root Zone Registry]]
- [[Public Technical Identifiers]]
- [[ICANN]]
- [[HTTP]]

## Open questions

- Which additional domains are reserved for documentation under RFC 2606 and RFC 6761?
- What operational guarantees, if any, does IANA make for DNS resolution of example domains?
- What are the exact criteria for an IANA-managed reserved domain?
- How should applications handle accidental or placeholder references to example domains in production configurations?

## Source

https://www.iana.org/help/example-domains