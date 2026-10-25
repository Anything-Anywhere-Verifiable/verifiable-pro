---
title: MCP Specification Removes Protocol Sessions and Tightens Authorization Rules
dek: The Model Context Protocol project published its 2026-07-28 specification on 28 July 2026. Each request now carries its own protocol version and client capabilities, and new rules tie authorization codes and stored credentials to the authorization server that issued them.
kind: news
topics: [agents-accountability]
layers: [agents]
event_date: 2026-07-28
published: 2026-10-20
agent: daily
evidence: [standard, announcement]
sources:
  - Key Changes, specification version 2026-07-28 | Model Context Protocol | 2026-07-28 | https://modelcontextprotocol.io/specification/2026-07-28/changelog
  - The 2026-07-28 Specification | Model Context Protocol Blog | 2026-07-28 | https://blog.modelcontextprotocol.io/posts/2026-07-28/
  - Specification, version 2026-07-28 | Model Context Protocol | 2026-07-28 | https://modelcontextprotocol.io/specification/2026-07-28
  - Authorization, specification version 2026-07-28 | Model Context Protocol | 2026-07-28 | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization
---

The Model Context Protocol (MCP) project released the 2026-07-28 revision of its specification on 28 July 2026, with updated software development kits.[^1, 2] MCP is an open protocol for connecting applications built on large language models to external data sources and tools. Clients inside these applications exchange JSON-RPC 2.0 messages with servers that provide context and capabilities.[^3]

The changelog lists the removal of protocol-level sessions as a major change. The initialization handshake and the `Mcp-Session-Id` header are gone. Each request now carries its protocol version and the client's capabilities in its metadata. Clients should identify themselves on every request, and servers should identify themselves in every result.[^1] The maintainers say any server instance behind a load balancer can now handle any request. They say servers that need state across calls should pass explicit handles as tool arguments.[^2]

Requests over the Streamable HTTP transport must also name the method and tool in `Mcp-Method` and `Mcp-Name` headers. The maintainers say this lets gateways route and authorize requests without parsing message bodies.[^1, 2]

The revision also tightens OAuth authorization. Authorization servers should include the issuer (`iss`) parameter defined in RFC 9207. Before redeeming an authorization code, clients must compare `iss`, if present, with the issuer they recorded. The maintainers say this closes an authorization-server mix-up hole.[^1, 2] Clients must store credentials per issuer and may not reuse them with a different authorization server. They must also re-register when the authorization server changes. Clients that use Dynamic Client Registration must specify an `application_type` to avoid OpenID Connect redirect URI conflicts. Dynamic Client Registration itself is now deprecated in favor of Client ID Metadata Documents, an OAuth Internet-Draft. It remains available for backward compatibility.[^1, 4] The authorization page says a future revision is expected to make the `iss` parameter mandatory for authorization servers.[^4]

:::analysis
Without sessions, each request carries its own protocol version. When clients follow the recommendation, it also carries their identity. A log of individual tool calls can therefore record that context without reconstructing connection state. That identity is self-declared, so evidence of whom an agent acts for still comes from authorization tokens. Tying codes and credentials to their issuer reduces the risk that they reach the wrong authorization server. Several of the new rules are recommendations, so what an operator can rely on depends on the client, server and authorization server implementations it uses.
:::

:::checked
On 20 October 2026 we read the 2026-07-28 changelog, the specification's overview and authorization pages, and the maintainers' release post. We did not review the software development kits, the enhancement proposals behind each change or any implementation. We test no systems ourselves.
:::
