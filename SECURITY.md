# Security notes

This repository is an educational example, not a production security
certification. Do not send sensitive or regulated data to model providers
without an approved data-handling design. Keep secrets in environment
variables or an appropriate secret manager; never commit them.

The demo API intentionally omits authentication, authorization, rate limiting,
and tenant isolation. Do not expose it to an untrusted network. Add those
controls, TLS, input/size limits, observability, and a threat model before any
real deployment. Retrieved text and model output are untrusted: validate
structured outputs, cite evidence, and require explicit authorization for
side-effecting tools. Cloud notebooks may create billable resources.
